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
PROBLEM_SIZE = 23           # Task difficulty (i.e. "n" in AlgoTune)
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
try:
    import numba
    from numba import njit
    NUMBA = True
except ImportError:
    NUMBA = False
if NUMBA:
    @njit(cache=True, fastmath=True)
    def _filter_smooth_numba(A, B, C, y, x0, tau):
        N = y.shape[0]
        m = y.shape[1]
        n = A.shape[1]
        p = B.shape[1]
        # Preallocate arrays
        x_pred = np.zeros((N+1, n))
        P_pred = np.zeros((N+1, n, n))
        x_filt = np.zeros((N+1, n))
        P_filt = np.zeros((N+1, n, n))
        # Covariances
        Q = B.dot(B.T)
        R = np.eye(m) / tau
        # Pseudo-inverse for B: M = (B^T B)^{-1} B^T
        BtB = B.T.dot(B)
        BtB_inv = np.linalg.inv(BtB)
        B_pinv = BtB_inv.dot(B.T)
        I_n = np.eye(n)
        # Initial state
        for i in range(n):
            x_pred[0, i] = x0[i]
        # Forward filter
        for t in range(N):
            Pt = P_pred[t]
            S = C.dot(Pt).dot(C.T) + R
            Sinv = np.linalg.inv(S)
            K = Pt.dot(C.T).dot(Sinv)
            innov = y[t] - C.dot(x_pred[t])
            x_filt[t] = x_pred[t] + K.dot(innov)
            P_filt[t] = (I_n - K.dot(C)).dot(Pt)
            x_pred[t+1] = A.dot(x_filt[t])
            P_pred[t+1] = A.dot(P_filt[t]).dot(A.T) + Q
        # Final update
        x_filt[N] = x_pred[N]
        P_filt[N] = P_pred[N]
        # Backward smoother
        x_smooth = np.zeros((N+1, n))
        x_smooth[N] = x_filt[N]
        for t in range(N-1, -1, -1):
            Pnext_inv = np.linalg.inv(P_pred[t+1])
            J = P_filt[t].dot(A.T).dot(Pnext_inv)
            x_smooth[t] = x_filt[t] + J.dot(x_smooth[t+1] - x_pred[t+1])
        # Recover noise estimates
        w_hat = np.zeros((N, p))
        v_hat = np.zeros((N, m))
        for t in range(N):
            diff = x_smooth[t+1] - A.dot(x_smooth[t])
            w_hat[t] = B_pinv.dot(diff)
            v_hat[t] = y[t] - C.dot(x_smooth[t])
        return x_smooth, w_hat, v_hat

    # Warm-up Numba compile (should use invertible covariances)
    try:
        _filter_smooth_numba(
            np.eye(1, dtype=np.float64),
            np.eye(1, dtype=np.float64),
            np.eye(1, dtype=np.float64),
            np.zeros((1, 1), dtype=np.float64),
            np.zeros(1, dtype=np.float64),
            1.0
        )
    except:
        pass
class Solver:
    def solve(self, problem, **kwargs):
        # Parse inputs
        if isinstance(problem, str):
            import json
            problem = json.loads(problem)
        A = np.array(problem["A"], dtype=np.float64)
        B = np.array(problem["B"], dtype=np.float64)
        C = np.array(problem["C"], dtype=np.float64)
        y = np.array(problem["y"], dtype=np.float64)
        x0 = np.array(problem["x_initial"], dtype=np.float64)
        tau = float(problem["tau"])
        # Filter & smooth
        if NUMBA:
            # Numba-accelerated Kalman filter, RTS smoother, and noise recovery
            x_smooth, w_hat_arr, v_hat_arr = _filter_smooth_numba(A, B, C, y, x0, tau)
            return {
                "x_hat": x_smooth.tolist(),
                "w_hat": w_hat_arr.tolist(),
                "v_hat": v_hat_arr.tolist(),
            }
        else:
            # Pure NumPy fallback: Kalman filter + RTS smoother
            N, m = y.shape
            n = A.shape[1]
            Q = B @ B.T
            R = np.eye(m) / tau
            x_pred = np.zeros((N+1, n))
            P_pred = np.zeros((N+1, n, n))
            x_filt = np.zeros((N+1, n))
            P_filt = np.zeros((N+1, n, n))
            x_pred[0] = x0
            I_n = np.eye(n)
            for t in range(N):
                Pt = P_pred[t]
                S = C @ Pt @ C.T + R
                K = Pt @ C.T @ np.linalg.inv(S)
                x_filt[t] = x_pred[t] + K @ (y[t] - C @ x_pred[t])
                P_filt[t] = (I_n - K @ C) @ Pt
                x_pred[t+1] = A @ x_filt[t]
                P_pred[t+1] = A @ P_filt[t] @ A.T + Q
            x_filt[N] = x_pred[N]
            P_filt[N] = P_pred[N]
            x_smooth = np.zeros((N+1, n))
            x_smooth[N] = x_filt[N]
            for t in range(N-1, -1, -1):
                Pnext = P_pred[t+1]
                J = P_filt[t] @ A.T @ np.linalg.inv(Pnext)
                x_smooth[t] = x_filt[t] + J @ (x_smooth[t+1] - x_pred[t+1])
            # Recover noise estimates
            # Enforce initial state constraint
            x_smooth[0] = x0
            diffs = x_smooth[1:] - x_smooth[:-1].dot(A.T)
            B_pinv = np.linalg.pinv(B)
            w_hat_arr = diffs.dot(B_pinv.T)
            v_hat_arr = y - x_smooth[:-1].dot(C.T)
            return {
                "x_hat": x_smooth.tolist(),
                "w_hat": w_hat_arr.tolist(),
                "v_hat": v_hat_arr.tolist(),
            }
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
