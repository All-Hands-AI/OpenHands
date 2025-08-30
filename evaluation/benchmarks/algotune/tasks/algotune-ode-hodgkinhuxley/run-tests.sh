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
PROBLEM_SIZE = 43           # Task difficulty (i.e. "n" in AlgoTune)
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
import numpy as np
from numba import njit

@njit(inline="always")
def alpha_m(V):
    # L'Hôpital's rule at V = -40
    if V == -40.0:
        return 1.0
    return 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))

@njit(inline="always")
def beta_m(V):
    return 4.0 * np.exp(-(V + 65.0) / 18.0)

@njit(inline="always")
def alpha_h(V):
    return 0.07 * np.exp(-(V + 65.0) / 20.0)

@njit(inline="always")
def beta_h(V):
    return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))

@njit(inline="always")
def alpha_n(V):
    # L'Hôpital's rule at V = -55
    if V == -55.0:
        return 0.1
    return 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))

@njit(inline="always")
def beta_n(V):
    return 0.125 * np.exp(-(V + 65.0) / 80.0)

@njit
def _rk4_integrate(t0, t1, y, C_m, g_Na, g_K, g_L,
                   E_Na, E_K, E_L, I_app, steps):
    dt = (t1 - t0) / steps
    V, m, h, n = y[0], y[1], y[2], y[3]
    for _ in range(steps):
        # k1
        I_Na = g_Na * m**3 * h * (V - E_Na)
        I_K = g_K * n**4 * (V - E_K)
        I_L = g_L * (V - E_L)
        k1_V = (I_app - I_Na - I_K - I_L) / C_m
        k1_m = alpha_m(V) * (1.0 - m) - beta_m(V) * m
        k1_h = alpha_h(V) * (1.0 - h) - beta_h(V) * h
        k1_n = alpha_n(V) * (1.0 - n) - beta_n(V) * n

        # k2
        V2 = V + 0.5 * dt * k1_V
        m2 = m + 0.5 * dt * k1_m
        h2 = h + 0.5 * dt * k1_h
        n2 = n + 0.5 * dt * k1_n
        I_Na = g_Na * m2**3 * h2 * (V2 - E_Na)
        I_K = g_K * n2**4 * (V2 - E_K)
        I_L = g_L * (V2 - E_L)
        k2_V = (I_app - I_Na - I_K - I_L) / C_m
        k2_m = alpha_m(V2) * (1.0 - m2) - beta_m(V2) * m2
        k2_h = alpha_h(V2) * (1.0 - h2) - beta_h(V2) * h2
        k2_n = alpha_n(V2) * (1.0 - n2) - beta_n(V2) * n2

        # k3
        V3 = V + 0.5 * dt * k2_V
        m3 = m + 0.5 * dt * k2_m
        h3 = h + 0.5 * dt * k2_h
        n3 = n + 0.5 * dt * k2_n
        I_Na = g_Na * m3**3 * h3 * (V3 - E_Na)
        I_K = g_K * n3**4 * (V3 - E_K)
        I_L = g_L * (V3 - E_L)
        k3_V = (I_app - I_Na - I_K - I_L) / C_m
        k3_m = alpha_m(V3) * (1.0 - m3) - beta_m(V3) * m3
        k3_h = alpha_h(V3) * (1.0 - h3) - beta_h(V3) * h3
        k3_n = alpha_n(V3) * (1.0 - n3) - beta_n(V3) * n3

        # k4
        V4 = V + dt * k3_V
        m4 = m + dt * k3_m
        h4 = h + dt * k3_h
        n4 = n + dt * k3_n
        I_Na = g_Na * m4**3 * h4 * (V4 - E_Na)
        I_K = g_K * n4**4 * (V4 - E_K)
        I_L = g_L * (V4 - E_L)
        k4_V = (I_app - I_Na - I_K - I_L) / C_m
        k4_m = alpha_m(V4) * (1.0 - m4) - beta_m(V4) * m4
        k4_h = alpha_h(V4) * (1.0 - h4) - beta_h(V4) * h4
        k4_n = alpha_n(V4) * (1.0 - n4) - beta_n(V4) * n4

        # Update
        V += (dt / 6.0) * (k1_V + 2*k2_V + 2*k3_V + k4_V)
        m += (dt / 6.0) * (k1_m + 2*k2_m + 2*k3_m + k4_m)
        h += (dt / 6.0) * (k1_h + 2*k2_h + 2*k3_h + k4_h)
        n += (dt / 6.0) * (k1_n + 2*k2_n + 2*k3_n + k4_n)

        # Clip gating variables
        if m < 0.0: m = 0.0
        elif m > 1.0: m = 1.0
        if h < 0.0: h = 0.0
        elif h > 1.0: h = 1.0
        if n < 0.0: n = 0.0
        elif n > 1.0: n = 1.0

    y[0], y[1], y[2], y[3] = V, m, h, n

class Solver:
    def solve(self, problem, **kwargs):
        # Unpack problem
        t0 = problem["t0"]
        t1 = problem["t1"]
        y = np.array(problem["y0"], dtype=np.float64)
        p = problem["params"]
        # Simulation parameters
        dt = 0.0125
        steps = int(np.ceil((t1 - t0) / dt))
        # Call compiled integrator
        _rk4_integrate(t0, t1, y,
                       p["C_m"], p["g_Na"], p["g_K"], p["g_L"],
                       p["E_Na"], p["E_K"], p["E_L"], p["I_app"],
                       steps)
        return y.tolist()
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
/usr/local/bin/pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
