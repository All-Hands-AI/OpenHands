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
PROBLEM_SIZE = 199           # Task difficulty (i.e. "n" in AlgoTune)
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
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import math
import numpy as np

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:  # pragma: no cover
    NUMBA_AVAILABLE = False

    def njit(*args, **kwargs):  # type: ignore
        def wrapper(func):
            return func
        return wrapper

@njit(fastmath=True, cache=True)
def _integrate_brusselator_numba(x0: float, y0: float, t0: float, t1: float,
                                 A: float, B: float, rtol: float, atol: float) -> Tuple[float, float]:
    # Precompute constants
    Bp1 = B + 1.0

    x = x0
    y = y0
    t = t0

    # Initial derivative
    x2 = x * x
    xy2 = x2 * y
    fx0 = A + xy2 - Bp1 * x
    fy0 = B * x - xy2

    # Initial step heuristic
    sx0 = atol + rtol * (x if x >= 0.0 else -x)
    sy0 = atol + rtol * (y if y >= 0.0 else -y)
    inv_sqrt2 = 0.7071067811865476
    d0 = math.hypot(x / sx0, y / sy0) * inv_sqrt2
    d1 = math.hypot(fx0 / sx0, fy0 / sy0) * inv_sqrt2
    if d0 < 1e-5 or d1 <= 1e-16:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1

    total = t1 - t0
    if h < 1e-12:
        h = 1e-12
    if h > total if total > 0.0 else h < total:
        h = total
    direction = 1.0 if total > 0.0 else -1.0
    h = h if total > 0.0 else -h

    # DP(5) coefficients
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

    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    bh1 = 5179.0 / 57600.0
    bh3 = 7571.0 / 16695.0
    bh4 = 393.0 / 640.0
    bh5 = -92097.0 / 339200.0
    bh6 = 187.0 / 2100.0
    bh7 = 1.0 / 40.0

    safety = 0.9
    min_factor = 0.2
    max_factor = 10.0
    inv_order = 0.2  # 1/5
    max_steps = 10000000

    steps = 0
    while True:
        steps += 1
        if steps > max_steps:
            break

        # Cap step to not overshoot t1
        dt = t1 - t
        if dt == 0.0:
            break
        if (dt > 0.0 and h > dt) or (dt < 0.0 and h < dt):
            h = dt

        # k1
        k1x = fx0
        k1y = fy0

        # k2
        x2 = x + h * a21 * k1x
        y2 = y + h * a21 * k1y
        x2x2 = x2 * x2
        xy2 = x2x2 * y2
        k2x = A + xy2 - Bp1 * x2
        k2y = B * x2 - xy2

        # k3
        x3 = x + h * (a31 * k1x + a32 * k2x)
        y3 = y + h * (a31 * k1y + a32 * k2y)
        x3x3 = x3 * x3
        xy3 = x3x3 * y3
        k3x = A + xy3 - Bp1 * x3
        k3y = B * x3 - xy3

        # k4
        x4 = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
        y4 = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
        x4x4 = x4 * x4
        xy4 = x4x4 * y4
        k4x = A + xy4 - Bp1 * x4
        k4y = B * x4 - xy4

        # k5
        x5 = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
        y5 = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
        x5x5 = x5 * x5
        xy5 = x5x5 * y5
        k5x = A + xy5 - Bp1 * x5
        k5y = B * x5 - xy5

        # k6
        x6 = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
        y6 = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
        x6x6 = x6 * x6
        xy6 = x6x6 * y6
        k6x = A + xy6 - Bp1 * x6
        k6y = B * x6 - xy6

        # 5th order solution
        y5x = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
        y5y = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

        # k7 at (t+h, y5)
        y5x2 = y5x * y5x
        xy7 = y5x2 * y5y
        k7x = A + xy7 - Bp1 * y5x
        k7y = B * y5x - xy7

        # 4th order solution using b_hat
        y4x = x + h * (bh1 * k1x + bh3 * k3x + bh4 * k4x + bh5 * k5x + bh6 * k6x + bh7 * k7x)
        y4y = y + h * (bh1 * k1y + bh3 * k3y + bh4 * k4y + bh5 * k5y + bh6 * k6y + bh7 * k7y)

        # Error estimate and norm
        ex = y5x - y4x
        ey = y5y - y4y
        ax = x if x >= 0.0 else -x
        ay = y if y >= 0.0 else -y
        a5x = y5x if y5x >= 0.0 else -y5x
        a5y = y5y if y5y >= 0.0 else -y5y
        sx = atol + rtol * (ax if ax >= a5x else a5x)
        sy = atol + rtol * (ay if ay >= a5y else a5y)
        dx = ex / sx
        dy = ey / sy
        err = math.hypot(dx, dy) * inv_sqrt2

        if err <= 1.0:
            # Accept step
            t += h
            x = y5x
            y = y5y
            # FSAL
            fx0 = k7x
            fy0 = k7y

            if t == t1:
                break

            # Step size update
            if err == 0.0:
                factor = max_factor
            else:
                factor = safety * (err ** (-inv_order))
                if factor < min_factor:
                    factor = min_factor
                elif factor > max_factor:
                    factor = max_factor
            h *= factor
        else:
            # Reject step
            factor = safety * (err ** (-inv_order))
            if factor < min_factor:
                factor = min_factor
            h *= factor

    return x, y

def _integrate_brusselator_py(x0: float, y0: float, t0: float, t1: float,
                              A: float, B: float, rtol: float, atol: float) -> Tuple[float, float]:
    # Fallback Python implementation (same as numba kernel)
    Bp1 = B + 1.0

    x = x0
    y = y0
    t = t0

    x2 = x * x
    xy2 = x2 * y
    fx0 = A + xy2 - Bp1 * x
    fy0 = B * x - xy2

    sx0 = atol + rtol * abs(x)
    sy0 = atol + rtol * abs(y)
    inv_sqrt2 = 0.7071067811865476
    d0 = math.hypot(x / sx0, y / sy0) * inv_sqrt2
    d1 = math.hypot(fx0 / sx0, fy0 / sy0) * inv_sqrt2
    if d0 < 1e-5 or d1 <= 1e-16:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1

    total = t1 - t0
    if h < 1e-12:
        h = 1e-12
    if (total > 0.0 and h > total) or (total < 0.0 and h < total):
        h = total
    direction = 1.0 if total > 0.0 else -1.0
    h = h if total > 0.0 else -h

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

    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    bh1 = 5179.0 / 57600.0
    bh3 = 7571.0 / 16695.0
    bh4 = 393.0 / 640.0
    bh5 = -92097.0 / 339200.0
    bh6 = 187.0 / 2100.0
    bh7 = 1.0 / 40.0

    safety = 0.9
    min_factor = 0.2
    max_factor = 10.0
    inv_order = 0.2
    max_steps = 10000000

    steps = 0
    while True:
        steps += 1
        if steps > max_steps:
            break

        dt = t1 - t
        if dt == 0.0:
            break
        if (dt > 0.0 and h > dt) or (dt < 0.0 and h < dt):
            h = dt

        k1x = fx0
        k1y = fy0

        x2 = x + h * a21 * k1x
        y2 = y + h * a21 * k1y
        x2x2 = x2 * x2
        xy2 = x2x2 * y2
        k2x = A + xy2 - Bp1 * x2
        k2y = B * x2 - xy2

        x3 = x + h * (a31 * k1x + a32 * k2x)
        y3 = y + h * (a31 * k1y + a32 * k2y)
        x3x3 = x3 * x3
        xy3 = x3x3 * y3
        k3x = A + xy3 - Bp1 * x3
        k3y = B * x3 - xy3

        x4 = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
        y4 = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
        x4x4 = x4 * x4
        xy4 = x4x4 * y4
        k4x = A + xy4 - Bp1 * x4
        k4y = B * x4 - xy4

        x5 = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
        y5 = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
        x5x5 = x5 * x5
        xy5 = x5x5 * y5
        k5x = A + xy5 - Bp1 * x5
        k5y = B * x5 - xy5

        x6 = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
        y6 = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
        x6x6 = x6 * x6
        xy6 = x6x6 * y6
        k6x = A + xy6 - Bp1 * x6
        k6y = B * x6 - xy6

        y5x = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
        y5y = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

        y5x2 = y5x * y5x
        xy7 = y5x2 * y5y
        k7x = A + xy7 - Bp1 * y5x
        k7y = B * y5x - xy7

        y4x = x + h * (bh1 * k1x + bh3 * k3x + bh4 * k4x + bh5 * k5x + bh6 * k6x + bh7 * k7x)
        y4y = y + h * (bh1 * k1y + bh3 * k3y + bh4 * k4y + bh5 * k5y + bh6 * k6y + bh7 * k7y)

        ex = y5x - y4x
        ey = y5y - y4y
        sx = atol + rtol * max(abs(x), abs(y5x))
        sy = atol + rtol * max(abs(y), abs(y5y))
        dx = ex / sx
        dy = ey / sy
        err = math.hypot(dx, dy) * inv_sqrt2

        if err <= 1.0:
            t += h
            x = y5x
            y = y5y
            fx0 = k7x
            fy0 = k7y

            if t == t1:
                break

            if err == 0.0:
                factor = max_factor
            else:
                factor = safety * (err ** (-inv_order))
                if factor < min_factor:
                    factor = min_factor
                elif factor > max_factor:
                    factor = max_factor
            h *= factor
        else:
            factor = safety * (err ** (-inv_order))
            if factor < min_factor:
                factor = min_factor
            h *= factor

    return x, y

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Any:
        # Extract problem data
        y0_list: List[float] = problem["y0"]
        t0: float = float(problem["t0"])
        t1: float = float(problem["t1"])
        params: Dict[str, float] = problem["params"]
        A: float = float(params["A"])
        B: float = float(params["B"])

        # Convert initial conditions
        x0 = float(y0_list[0])
        y0 = float(y0_list[1])

        # If no integration needed
        if t1 == t0:
            return np.array([x0, y0], dtype=float)

        # Integration settings (tighter than checker tolerance for safety)
        rtol = 1e-8
        atol = 1e-8

        if NUMBA_AVAILABLE:
            x, y = _integrate_brusselator_numba(x0, y0, t0, t1, A, B, rtol, atol)
        else:
            x, y = _integrate_brusselator_py(x0, y0, t0, t1, A, B, rtol, atol)

        return np.array([x, y], dtype=float)
EOF

# --- Step 4: Run performance test on the new solver ---
# Execute pytest and parse the output to find the "Calculated Speedup".
# The result is saved to a file. If the test fails or the speedup
# cannot be determined, it defaults to "1.0".
echo "Running performance test..."
(set -o pipefail; pytest -s /workspace/test_outputs.py 2>&1 | tee /workspace/test_outputs.log | tee /dev/stderr | grep "Calculated Speedup" | awk '{print $3}' | sed 's/x$//' > /workspace/.best_solver_speedup.txt) \
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
pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
