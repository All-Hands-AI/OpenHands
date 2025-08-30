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
PROBLEM_SIZE = 210           # Task difficulty (i.e. "n" in AlgoTune)
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

from typing import Any, Dict, List

import numpy as np
from scipy.optimize import linprog

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, List[float]]:
        """
        Solve the LP Box problem:
            minimize    c^T x
            subject to  A x <= b
                        0 <= x <= 1

        Parameters
        ----------
        problem : dict
            Dictionary with keys:
              - "c": list of length n (objective coefficients)
              - "A": list of m lists (inequality matrix)
              - "b": list of length m (inequality rhs)

        Returns
        -------
        dict
            {"solution": list of length n} the optimal primal solution.
        """
        c = np.asarray(problem["c"], dtype=float).ravel()
        n = c.size

        # Handle A, b possibly missing or empty
        A_list = problem.get("A", [])
        b_list = problem.get("b", [])

        if A_list is None:
            A = np.empty((0, n), dtype=float)
            b = np.empty((0,), dtype=float)
        else:
            A = np.asarray(A_list, dtype=float)
            if A.ndim == 1 and A.size != 0:
                A = A.reshape(1, -1)
            if A.size == 0:
                A = np.empty((0, n), dtype=float)
            else:
                # Ensure correct shape if possible
                if A.shape[1] != n:
                    A = A.reshape(-1, n)
            b = (
                np.asarray(b_list, dtype=float).ravel()
                if b_list is not None
                else np.empty((0,), dtype=float)
            )

        m = A.shape[0]

        # Fast path: no inequality constraints -> box-only LP
        if m == 0:
            # Minimization over [0,1]^n: choose x_i = 1 if c_i < 0 else 0
            x = np.where(c < 0.0, 1.0, 0.0)
            return {"solution": x.tolist()}

        # Quick feasibility checks for trivial candidates
        x0 = np.where(c < 0.0, 1.0, 0.0)  # Box-optimum ignoring Ax<=b
        # Check x0 feasibility
        if A.shape[1] == n and b.size == m:
            Ax0 = A @ x0
            if np.all(Ax0 <= b + 1e-12):
                return {"solution": x0.tolist()}
        # Check all-zero feasibility (often feasible and optimal when c >= 0)
        x_zero = np.zeros(n, dtype=float)
        Ax_zero_ok = False
        if A.shape[1] == n and b.size == m:
            Ax_zero_ok = np.all((A @ x_zero) <= b + 1e-12)
            if Ax_zero_ok and np.all(c >= 0):
                return {"solution": x_zero.tolist()}
            # Check all-ones feasibility fast path when objective prefers ones
            if np.all(c <= 0.0):
                x_one = np.ones(n, dtype=float)
                if np.all((A @ x_one) <= b + 1e-12):
                    return {"solution": x_one.tolist()}

        # Remove constraints that are redundant given 0<=x<=1:
        # For row i, max over box is sum(max(A[i,j],0)). If this <= b_i, constraint is redundant.
        # Vectorized computation of positive row sums
        pos_row_sum = np.sum(np.maximum(A, 0.0), axis=1)
        # Keep only potentially active constraints
        keep = pos_row_sum > (b + 1e-12)
        if np.any(~keep):
            A = A[keep]
            b = b[keep]
            m = A.shape[0]
            if m == 0:
                # All constraints redundant; return box-only optimum
                x = np.where(c < 0.0, 1.0, 0.0)
                return {"solution": x.tolist()}
            # Re-check feasibility of x0 on the reduced system
            Ax0 = A @ x0
            if np.all(Ax0 <= b + 1e-12):
                return {"solution": x0.tolist()}
            if Ax_zero_ok:
                Ax_zero_red_ok = np.all((A @ x_zero) <= b + 1e-12)
                if Ax_zero_red_ok and np.all(c >= 0):
                    return {"solution": x_zero.tolist()}

        bounds = [(0.0, 1.0)] * n

        # Variable fixing using column monotonicity:
        # - If column j is <= 0 for all rows and c_j < 0, set x_j = 1 (improves objective and cannot hurt feasibility).
        # - If column j is >= 0 for all rows and c_j >= 0, set x_j = 0 (cannot hurt feasibility and is objective-preferable).
        if m > 0:
            col_all_nonpos = np.all(A <= 0.0, axis=0)
            col_all_nonneg = np.all(A >= 0.0, axis=0)
            fix_one_mask = col_all_nonpos & (c < 0.0)
            fix_zero_mask = col_all_nonneg & (c >= 0.0)

            if np.any(fix_one_mask) or np.any(fix_zero_mask):
                x_full = np.zeros(n, dtype=float)
                x_full[fix_one_mask] = 1.0  # fix to 1 where safe and beneficial
                # zeros already set for fix_zero_mask, and remain 0 for others until solved

                free_mask = ~(fix_one_mask | fix_zero_mask)
                if np.any(free_mask):
                    # Reduce problem
                    A_red = A[:, free_mask]
                    # Adjust rhs for fixed ones (making constraints looser)
                    if np.any(fix_one_mask):
                        b_red = b - A[:, fix_one_mask] @ np.ones(int(np.count_nonzero(fix_one_mask)))
                    else:
                        b_red = b.copy()
                    c_red = c[free_mask]
                    x0_free = (c_red < 0.0).astype(float)

                    # Second-stage redundancy elimination on reduced system
                    if A_red.shape[0] > 0:
                        pos_row_sum_red = np.sum(np.maximum(A_red, 0.0), axis=1)
                        keep_red = pos_row_sum_red > (b_red + 1e-12)
                        if np.any(~keep_red):
                            A_red = A_red[keep_red]
                            b_red = b_red[keep_red]

                    if A_red.shape[0] == 0:
                        # No active constraints remain
                        x_full[free_mask] = x0_free
                        return {"solution": np.clip(x_full, 0.0, 1.0).tolist()}

                    # Quick checks on reduced problem
                    if np.all(A_red @ x0_free <= b_red + 1e-12):
                        x_full[free_mask] = x0_free
                        return {"solution": np.clip(x_full, 0.0, 1.0).tolist()}

                    if np.all(c_red >= 0.0):
                        x_zero_free = np.zeros_like(c_red)
                        if np.all(A_red @ x_zero_free <= b_red + 1e-12):
                            x_full[free_mask] = x_zero_free
                            return {"solution": x_full.tolist()}

                    # Solve reduced LP
                    bounds_red = [(0.0, 1.0)] * int(np.count_nonzero(free_mask))
                    res = linprog(c_red, A_ub=A_red, b_ub=b_red, bounds=bounds_red, method="highs")

                    x_free_sol = res.x if (res.success and (res.x is not None)) else x0_free
                    x_full[free_mask] = x_free_sol
                    # Numerical safety: clip to box
                    x_full = np.clip(x_full, 0.0, 1.0)
                    return {"solution": x_full.tolist()}
                else:
                    # All variables fixed
                    return {"solution": x_full.tolist()}

        # Solve with HiGHS on the (possibly reduced) original system
        res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

        x_res = res.x if (res.success and (res.x is not None)) else x0

        # Numerical safety: clip to box
        x_res = np.clip(np.asarray(x_res, dtype=float), 0.0, 1.0)

        return {"solution": x_res.tolist()}
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
