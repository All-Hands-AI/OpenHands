#!/bin/bash

# This script is designed to first test a candidate "best" solver for performance,
# record its speedup, and then run a final validation test using the original solver.

# --- Step 1: Create the test file ---
# This file contains the tests that will be run against the solvers.
# It's created first to be available for both test runs.
cat > /workspace/test_outputs.py << 'EOF'
# test_outputs.py
import importlib.util
import logging
import time
from pathlib import Path
from typing import Callable, Any, List, Tuple, Union
import numpy as np
import pytest

# --- Configuration ---
SOLVER_PATH = Path("/workspace/solver.py")
BEST_SOLVER_SPEEDUP_FILE = Path('/workspace/.best_solver_speedup.txt')

# --- Problem Generation and Dynamic Measurement Parameters ---
PROBLEM_SIZE = 15           # Task difficulty (i.e. "n" in AlgoTune)
MAX_SAMPLES = 200            # Maximum number of problems to test
MIN_SAMPLES = 30             # Minimum samples before first stability check
STABILITY_BATCH_SIZE = 10    # Check for stability every N new samples
STABILITY_THRESHOLD = 0.01   # Stop when median changes by less than 1%
IQR_STABILITY_THRESHOLD = 0.05 # Stop when IQR changes by less than 5%

# --- Setup ---
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from evaluator import Task
task = Task()


@pytest.fixture(scope="module")
def solver_instance() -> Any:
    """Loads the user's 'Solver' class from solver.py."""
    if not SOLVER_PATH.exists():
        pytest.fail(f"Solver file not found at {SOLVER_PATH}")
    
    spec = importlib.util.spec_from_file_location("solver", SOLVER_PATH)
    solver_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solver_module)
    return solver_module.Solver()

@pytest.fixture(scope="module")
def problem_set() -> List[Any]:
    """Generates a fixed, reproducible set of up to MAX_SAMPLES problems."""
    logger.info(f"Generating {MAX_SAMPLES} unique problems for performance testing...")
    problems = []
    for i in range(MAX_SAMPLES):
        # Use the index 'i' as the seed for reproducibility.
        problem = task.generate_problem(n=PROBLEM_SIZE, random_seed=i)
        problems.append(problem)
    return problems

def _measure_stable_median_time(solve_func: Callable[[Any], Any], problems: List[Any]) -> Tuple[Union[float, str], int]:
    """
    Measures the median execution time, adding samples until both the median
    and the Interquartile Range (IQR) of the timings stabilize.
    """
    measured_times = []
    old_median = 0.0
    old_iqr = 0.0

    for i, problem in enumerate(problems):
        start = time.perf_counter_ns()
        solution = solve_func(problem)
        end = time.perf_counter_ns()

        if not task.is_solution(problem, solution):
            return "Solver produced an invalid solution.", i + 1

        measured_times.append(end - start)

        num_samples = i + 1
        if num_samples >= MIN_SAMPLES and (num_samples - MIN_SAMPLES) % STABILITY_BATCH_SIZE == 0:
            # Calculate current median and IQR
            current_median = np.median(measured_times)
            q75, q25 = np.percentile(measured_times, [75, 25])
            current_iqr = q75 - q25

            # Check for stability only if we have previous values to compare against
            if old_median > 0 and old_iqr > 0:
                relative_median_change = abs(current_median - old_median) / old_median
                # Handle case where IQR is zero to avoid division by zero
                relative_iqr_change = abs(current_iqr - old_iqr) / old_iqr if old_iqr > 0 else 0

                # The new, more robust stability condition
                median_is_stable = relative_median_change < STABILITY_THRESHOLD
                iqr_is_stable = relative_iqr_change < IQR_STABILITY_THRESHOLD
                
                if median_is_stable and iqr_is_stable:
                    logger.info(
                        f"Measurements stabilized after {num_samples} samples. "
                        f"(Median change < {STABILITY_THRESHOLD*100:.1f}%, "
                        f"IQR change < {IQR_STABILITY_THRESHOLD*100:.1f}%)"
                    )
                    return current_median, num_samples
            
            old_median = current_median
            old_iqr = current_iqr

    # Fallback if stability wasn't reached by MAX_SAMPLES
    final_median = np.median(measured_times) if measured_times else 0
    logger.warning(f"Measurements did not stabilize. Reporting result from all {len(measured_times)} samples.")
    return final_median, len(measured_times)

@pytest.fixture(scope="module")
def performance_results(solver_instance, problem_set) -> dict:
    """
    Calculates performance by running the solver and baseline until timing stabilizes.
    """
    logger.info("Calculating performance with dynamic sampling...")

    # Measure time for the user's solver dynamically
    median_solver_time, solver_samples = _measure_stable_median_time(
        solver_instance.solve,
        problems=problem_set
    )
    
    # Measure time for the baseline dynamically on the exact same problem set
    median_baseline_time, baseline_samples = _measure_stable_median_time(
        task.solve,
        problems=problem_set
    )

    if isinstance(median_solver_time, str):
        validity = median_solver_time
        median_solver_time = 0.0
        median_baseline_time = 0.0
        speedup = 0.0
    else:
        validity = True
        speedup = median_baseline_time / median_solver_time if median_solver_time > 0 else float('inf')

    print(f"\n--- Performance Summary ---")
    print(f"Validity: {validity}")
    print(f"Baseline Median Time: {median_baseline_time / 1e9:.4f}s (over {baseline_samples} samples)")
    print(f"Solver Median Time:   {median_solver_time / 1e9:.4f}s (over {solver_samples} samples)")
    print(f"Calculated Speedup:   {speedup:.2f} x")
    print("Keep improving your result!")
    print(f"---------------------------")
    
    return {"speedup": speedup, "validity": validity}


def test_solver_exists():
    """Checks if the solver.py file exists."""
    assert SOLVER_PATH.is_file(), f"Solver file not found at {SOLVER_PATH}"

def test_solver_is_solution(performance_results):
    assert performance_results['validity'] == True, performance_results['validity']

def test_solver_is_faster_than_baseline(performance_results):
    """
    Checks if the solver is at least as fast as the baseline.
    """
    speedup = performance_results["speedup"]
    assert speedup >= 0.9   # A tolerance margin


def test_solver_meets_target_speedup(performance_results):
    """Checks if the solver meets the speedup target from the best submission."""
    if not BEST_SOLVER_SPEEDUP_FILE.exists():
        pytest.skip(f"No best speedup file found at {BEST_SOLVER_SPEEDUP_FILE}. Skipping target test.")
    
    try:
        target_speedup = float(BEST_SOLVER_SPEEDUP_FILE.read_text(encoding='utf-8').strip())
    except (ValueError, FileNotFoundError):
        pytest.skip("Could not read target speedup. Skipping target test.")

    speedup = performance_results["speedup"]
    assert speedup >= target_speedup * 0.9  # A tolerance margin


# For agent to use 
if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
EOF

# --- Step 2: Backup the original solver ---
# Copy the existing solver.py to a backup location before overwriting it.
# This preserves the original code for the final test run.
echo "Backing up original solver..."
cp /workspace/solver.py /workspace/solver.py.bak

# --- Step 3: Write the new "best" solver ---
# The new solver code is written to /workspace/solver.py. This file will be
# used for the performance evaluation in the next step.
cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict, List

try:
    from numba import njit  # type: ignore
except Exception:

    def njit(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

@njit(cache=True, fastmath=True)
def _integrate_dp45(
    t0: float,
    t1: float,
    v0: float,
    w0: float,
    a: float,
    b: float,
    c: float,
    I: float,
    rtol: float,
    atol: float,
) -> tuple:
    # Dormand–Prince RK45 coefficients used (a21..a65, b, b*)
    a21 = 1.0 / 5.0

    a31 = 3.0 / 40.0
    a32 = 9.0 / 40.0

    a41 = 44.0 / 45.0
    a42 = -56.0 / 15.0
    a43 = 32.0 / 9.0

    a51 = 19372.0 / 6561.0
    a52 = -25360.0 / 2187.0
    a53 = 64448.0 / 6561.0
    a54 = -212.0 / 729.0

    a61 = 9017.0 / 3168.0
    a62 = -355.0 / 33.0
    a63 = 46732.0 / 5247.0
    a64 = 49.0 / 176.0
    a65 = -5103.0 / 18656.0

    # 5th order solution weights (b)
    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    # Error weights e = b - bs for embedded 4th order estimate
    e1 = 71.0 / 57600.0
    e3 = -71.0 / 16695.0
    e4 = 71.0 / 1920.0
    e5 = -17253.0 / 339200.0
    e6 = 22.0 / 525.0
    e7 = -1.0 / 40.0

    # Precompute constants for RHS
    inv3 = 1.0 / 3.0
    ab = a * b
    ac = a * c

    t = t0
    v = float(v0)
    w = float(w0)
    direction = 1.0 if t1 >= t0 else -1.0
    t_end = t1

    # Initial derivative k1 = f(v, w)
    v2 = v * v
    v3 = v2 * v
    k1v = v - inv3 * v3 - w + I
    k1w = ab * v - ac * w

    # Initial step size heuristic
    sv0 = atol + rtol * (v if v >= 0.0 else -v)
    sw0 = atol + rtol * (w if w >= 0.0 else -w)
    d0 = ((v / sv0) ** 2 + (w / sw0) ** 2) ** 0.5
    d1 = ((k1v / sv0) ** 2 + (k1w / sw0) ** 2) ** 0.5
    if d0 < 1e-5 or d1 < 1e-5:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1
    rem = t_end - t
    if rem < 0.0:
        rem = -rem
    if h * direction > 0.0:
        h = (rem if rem < h else h) * direction
    else:
        h = (rem if rem < (h if h >= 0.0 else -h) else (h if h >= 0.0 else -h)) * direction

    SAFETY = 0.9
    MIN_FACTOR = 0.2
    MAX_FACTOR = 20.0
    ORDER = 5.0
    INV_SQRT2 = 0.7071067811865476

    # Integrate until reaching t1
    while (t - t_end) * direction + 1e-18 < 0.0:
        # Ensure we don't step past the end
        if (t + h - t_end) * direction > 0.0:
            h = t_end - t

        # Stage 2
        y2v = v + h * (a21 * k1v)
        y2w = w + h * (a21 * k1w)
        z = y2v
        z2 = z * z
        z3 = z2 * z
        k2v = z - inv3 * z3 - y2w + I
        k2w = ab * y2v - ac * y2w

        # Stage 3
        y3v = v + h * (a31 * k1v + a32 * k2v)
        y3w = w + h * (a31 * k1w + a32 * k2w)
        z = y3v
        z2 = z * z
        z3 = z2 * z
        k3v = z - inv3 * z3 - y3w + I
        k3w = ab * y3v - ac * y3w

        # Stage 4
        y4v = v + h * (a41 * k1v + a42 * k2v + a43 * k3v)
        y4w = w + h * (a41 * k1w + a42 * k2w + a43 * k3w)
        z = y4v
        z2 = z * z
        z3 = z2 * z
        k4v = z - inv3 * z3 - y4w + I
        k4w = ab * y4v - ac * y4w

        # Stage 5
        y5v = v + h * (a51 * k1v + a52 * k2v + a53 * k3v + a54 * k4v)
        y5w = w + h * (a51 * k1w + a52 * k2w + a53 * k3w + a54 * k4w)
        z = y5v
        z2 = z * z
        z3 = z2 * z
        k5v = z - inv3 * z3 - y5w + I
        k5w = ab * y5v - ac * y5w

        # Stage 6
        y6v = v + h * (a61 * k1v + a62 * k2v + a63 * k3v + a64 * k4v + a65 * k5v)
        y6w = w + h * (a61 * k1w + a62 * k2w + a63 * k3w + a64 * k4w + a65 * k5w)
        z = y6v
        z2 = z * z
        z3 = z2 * z
        k6v = z - inv3 * z3 - y6w + I
        k6w = ab * y6v - ac * y6w

        # 5th order solution
        y5_v = v + h * (b1 * k1v + b3 * k3v + b4 * k4v + b5 * k5v + b6 * k6v)
        y5_w = w + h * (b1 * k1w + b3 * k3w + b4 * k4w + b5 * k5w + b6 * k6w)

        # 7th stage at (t + h, y5) for FSAL and error estimate
        z = y5_v
        z2 = z * z
        z3 = z2 * z
        k7v = z - inv3 * z3 - y5_w + I
        k7w = ab * y5_v - ac * y5_w

        # Embedded error estimate directly via weights e
        err_v = h * (e1 * k1v + e3 * k3v + e4 * k4v + e5 * k5v + e6 * k6v + e7 * k7v)
        err_w = h * (e1 * k1w + e3 * k3w + e4 * k4w + e5 * k5w + e6 * k6w + e7 * k7w)

        # Scaled RMS error norm
        av = v if v >= 0.0 else -v
        aw = w if w >= 0.0 else -w
        ayv = y5_v if y5_v >= 0.0 else -y5_v
        ayw = y5_w if y5_w >= 0.0 else -y5_w
        scale_v = atol + rtol * (av if av > ayv else ayv)
        scale_w = atol + rtol * (aw if aw > ayw else ayw)
        ev = err_v / scale_v
        ew = err_w / scale_w
        err_norm = (ev * ev + ew * ew) ** 0.5
        err_norm *= INV_SQRT2  # 1/sqrt(2)

        if err_norm <= 1.0:
            # Accept step
            t += h
            v = y5_v
            w = y5_w
            # FSAL: reuse k7 as next k1
            k1v, k1w = k7v, k7w
        # Else: reject step, keep (t, v, w) and reuse k1

        # Step size adaptation using standard exponent -1/ORDER
        if err_norm == 0.0:
            factor = MAX_FACTOR
        else:
            factor = SAFETY * err_norm ** (-1.0 / ORDER)
            if factor < MIN_FACTOR:
                factor = MIN_FACTOR
            elif factor > MAX_FACTOR:
                factor = MAX_FACTOR
        h *= factor

        # Prevent stagnation on tiny step sizes
        ah = h if h >= 0.0 else -h
        if ah < 1e-16:
            break

    return v, w

class Solver:
    __slots__ = ()

    def __init__(self) -> None:
        # Warm up numba compilation outside of solve timing.
        try:
            _integrate_dp45(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1e-8, 1e-8)
        except Exception:
            pass

    def solve(self, problem: Dict[str, Any], **kwargs) -> List[float]:
        # Extract inputs without NumPy overhead
        y0 = problem["y0"]
        v0 = float(y0[0])
        w0 = float(y0[1])
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        params = problem["params"]
        a = float(params["a"])
        b = float(params["b"])
        c = float(params["c"])
        I = float(params["I"])

        # Trivial case
        if t1 == t0:
            return [v0, w0]

        # Tolerances matching reference-level accuracy
        rtol = 1e-8
        atol = 1e-8

        v_final, w_final = _integrate_dp45(t0, t1, v0, w0, a, b, c, I, rtol, atol)
        return [float(v_final), float(w_final)]
EOF

# --- Step 4: Run performance test on the new solver ---
# Execute pytest and parse the output to find the "Calculated Speedup".
# The result is saved to a file. If the test fails or the speedup
# cannot be determined, it defaults to "1.0".
echo "Running performance test..."
(set -o pipefail; /usr/local/bin/pytest -s /workspace/test_outputs.py 2>&1 | tee /workspace/test_outputs.log | tee /dev/stderr | grep "Calculated Speedup" | awk '{print $3}' | sed 's/x$//' > /workspace/.best_solver_speedup.txt) \
|| echo "1.0" > /workspace/.best_solver_speedup.txt

# --- Output Speedup and Solver Code for Review ---
echo "--- TARGET SPEEDUP ---"
cat /workspace/.best_solver_speedup.txt
echo "--- TARGET SPEED END ---"

# --- Step 5: Restore the original solver ---
# Move the backup file back to /workspace/solver.py, overwriting the
# temporary "best" solver.
echo "Restoring original solver..."
rm -rf /workspace/solver.py
mv /workspace/solver.py.bak /workspace/solver.py

# --- Step 6: Run final tests on the original solver ---
# Now that the original solver is restored, run the final pytest
# validation to ensure correctness.
echo "Running final validation on original solver..."
/usr/local/bin/pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
