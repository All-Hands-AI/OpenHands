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
from typing import Any, Dict
import json

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Solve the optimal advertising problem via a fast LP reformulation.

        Reformulation:
            Introduce variables t_i representing realized revenue for ad i.
            Maximize sum_i t_i subject to:
              - t_i <= B_i
              - t_i <= R_i * sum_t P_it * D_it
              - D_it >= 0
              - sum_i D_it <= T_t  (capacity per time slot)
              - sum_t D_it >= c_i  (min display requirement per ad)

        We encode the LP for SciPy's HiGHS:
            Variables: x = [vec(D) ; t], size m*n + m
            Objective: maximize sum(t) -> minimize -sum(t)

        :param problem: Dictionary with problem parameters
        :return: Solution dictionary
        """
        # Allow JSON string input for eval_input convenience
        if isinstance(problem, str):
            try:
                problem = json.loads(problem)
            except Exception:
                return {"status": "invalid_input_format", "optimal": False}

        # Extract and validate inputs
        P = np.asarray(problem["P"], dtype=float)
        R = np.asarray(problem["R"], dtype=float)
        B = np.asarray(problem["B"], dtype=float)
        c = np.asarray(problem["c"], dtype=float)
        T = np.asarray(problem["T"], dtype=float)

        m, n = P.shape
        if R.shape != (m,) or B.shape != (m,) or c.shape != (m,) or T.shape != (n,):
            return {
                "status": "invalid_input_shapes",
                "optimal": False,
            }

        num_D = m * n
        num_vars = num_D + m

        # Objective: minimize -sum(t)
        obj = np.zeros(num_vars, dtype=float)
        obj[num_D:] = -1.0

        # Build A_ub and b_ub in three blocks using vectorized construction.
        # Block 1: Capacity constraints per time t: sum_i D_it <= T_t  (n rows)
        rows_cap = np.repeat(np.arange(n), m)
        cols_cap = np.tile(np.arange(m) * n, n) + np.repeat(np.arange(n), m)
        data_cap = np.ones_like(cols_cap, dtype=float)
        b_cap = T

        # Block 2: Minimum display constraints per ad i: -sum_t D_it <= -c_i  (m rows)
        rows_min = np.repeat(np.arange(m) + n, n)
        cols_min = np.arange(num_D)
        data_min = -np.ones_like(cols_min, dtype=float)
        b_min = -c

        # Block 3: Revenue linking per ad i:
        # t_i - R_i * sum_t P_it * D_it <= 0  (m rows)
        rows_rev_D_all = np.repeat(np.arange(m) + n + m, n)
        coeff_rev_D_all = (-R[:, None] * P).ravel(order="C")
        cols_rev_D_all = np.arange(num_D)
        # Filter out zero coefficients to reduce matrix size
        mask = coeff_rev_D_all != 0.0
        rows_rev_D = rows_rev_D_all[mask]
        cols_rev_D = cols_rev_D_all[mask]
        data_rev_D = coeff_rev_D_all[mask]
        # t-part (diagonal 1's on t variables)
        rows_rev_t = np.arange(m) + n + m
        cols_rev_t = num_D + np.arange(m)
        data_rev_t = np.ones(m, dtype=float)
        b_rev = np.zeros(m, dtype=float)

        # Concatenate all blocks
        rows = np.concatenate([rows_cap, rows_min, rows_rev_D, rows_rev_t])
        cols = np.concatenate([cols_cap, cols_min, cols_rev_D, cols_rev_t])
        data = np.concatenate([data_cap, data_min, data_rev_D, data_rev_t])
        b_ub = np.concatenate([b_cap, b_min, b_rev])

        A_ub = coo_matrix((data, (rows, cols)), shape=(n + m + m, num_vars)).tocsr()

        # Variable bounds
        bounds = []
        # D_it >= 0, no explicit upper bound
        bounds.extend([(0.0, None) for _ in range(num_D)])
        # 0 <= t_i <= B_i (if B_i is finite), else upper bound None
        for i in range(m):
            Bi = float(B[i])
            ub = None if not np.isfinite(Bi) else Bi
            bounds.append((0.0, ub))

        # Solve LP using HiGHS
        res = linprog(c=obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        if not res.success:
            return {
                "status": f"linprog_failed: {res.message}",
                "optimal": False,
            }

        x = res.x
        D_opt = x[:num_D].reshape((m, n))

        # Numerical cleanup: clip tiny negatives to zero
        if np.any(D_opt < 0):
            D_opt = np.maximum(D_opt, 0.0)

        # Compute clicks and revenue
        clicks = np.einsum("ij,ij->i", P, D_opt)
        revenue_per_ad = np.minimum(R * clicks, B)
        total_revenue = float(np.sum(revenue_per_ad))

        return {
            "status": "optimal",
            "optimal": True,
            "displays": D_opt.tolist(),
            "clicks": clicks.tolist(),
            "revenue_per_ad": revenue_per_ad.tolist(),
            "total_revenue": total_revenue,
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
