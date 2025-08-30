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
PROBLEM_SIZE = 318           # Task difficulty (i.e. "n" in AlgoTune)
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
# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import ast
import logging

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import expm



class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the MatrixExponentialSparse task.

        In this task, you are given a square sparse matrix A.
        The task is to compute its matrix exponential exp(A), using the Pade approximation.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, sparse.spmatrix]:
        """
        Generate a random square sparse matrix A of size n x n.

        Although n is provided for scaling, the generated problem contains only the matrix.
        The dimension of the matrix can be inferred directly from the matrix itself.

        :param n: The dimension of the square matrix.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the matrix exponential problem with key:
                 "matrix": A numpy sparse array in csc format and of shape (n, n), representing the square matrix A.
        """
        density = 0.01
        # Ensure n is at least 100 for the problem to be meaningful
        n = max(100, n)

        logging.debug(
            f"Generating matrix exponential problem with n={n} and random_seed={random_seed}"
        )
        rng = np.random.default_rng(random_seed)

        # Generate a random n x n sparse matrix with real entries. The csc format is the most efficient for the exponential.
        matrix = sparse.random(n, n, density=density, format="csc", data_rvs=rng.standard_normal)

        problem = {"matrix": matrix}
        logging.debug("Generated matrix exponential problem.")

        return problem

    def solve(self, problem: dict[str, sparse.spmatrix]) -> sparse.spmatrix:
        """
        Solve the sparse matrix exponential problem by computing exp(A).
        Uses scipy.sparse.linalg.expm to compute the matrix exponential.

        :param problem: A dictionary representing the matrix exponential problem.
        :return: The matrix exponential of the input matrix A, represented as sparse matrix.
        """
        A = problem["matrix"]
        solution = expm(A)

        return solution

    def is_solution(self, problem: dict[str, np.ndarray], solution: sparse.spmatrix) -> bool:
        """
        Check if the provided solution is a valid and accurate matrix exponential.

        Checks:
            1. Proposed exponential matrix dimensions match the input matrix.
            2. Proposed exponential matrix values are close to the reference calculation.

        :param problem: Dictionary containing the input matrix "matrix".
        :param solution: Sparse matrix representing the proposed solution.
        :return: True if the solution is valid and accurate, False otherwise.
        """
        A = problem.get("matrix")
        if A is None:
            logging.error("Problem dictionary missing 'matrix' key.")
            return False

        if not isinstance(solution, sparse.spmatrix):
            logging.error("Solution is not a sparse matrix.")
            return False

        if not sparse.isspmatrix_csc(solution):
            logging.error("Solution is not in CSC format.")
            return False

        if tuple(solution.shape) != tuple(A.shape):
            # Attempt to parse A.shape if it's a string representation (e.g., "[313, 313]")
            # that might be causing a mismatch with solution.shape (a tuple of ints).
            parsed_a_shape_for_comparison = None
            a_shape_original = A.shape

            if isinstance(a_shape_original, str):
                try:
                    evaluated_shape = ast.literal_eval(a_shape_original)
                    if isinstance(evaluated_shape, list | tuple):
                        parsed_a_shape_for_comparison = tuple(int(x) for x in evaluated_shape)
                except (ValueError, SyntaxError, TypeError):
                    logging.error(
                        f"Input matrix shape A.shape ('{a_shape_original}') is a string but could not be properly parsed and converted to a tuple of integers."
                    )
                    return False  # Fail early if string parsing/conversion fails
            elif isinstance(a_shape_original, list | tuple):
                try:
                    parsed_a_shape_for_comparison = tuple(int(x) for x in a_shape_original)
                except (ValueError, TypeError):
                    logging.error(
                        f"Input matrix shape A.shape ('{a_shape_original}') could not be converted to a tuple of integers."
                    )
                    return False  # Fail if list/tuple elements are not integers

            if parsed_a_shape_for_comparison is None:
                # This path taken if A.shape was not str/list/tuple or previous conversions failed silently (which they shouldn't with current logic)
                logging.error(
                    f"Could not determine a comparable tuple of integers from input matrix shape A.shape ('{a_shape_original}', type: {type(a_shape_original)}). Cannot reliably compare with solution shape."
                )
                return False

            # Perform the comparison with the parsed shape
            if solution.shape != parsed_a_shape_for_comparison:
                logging.error(
                    f"Solution shape {solution.shape} (type: {type(solution.shape)}) does not match input matrix shape {A.shape} (type: {type(A.shape)}, compared as {parsed_a_shape_for_comparison})."
                )
                return False
            # If shapes match after parsing, proceed to other checks.

        # Recompute the reference solution
        try:
            expA_ref = expm(A)
        except Exception as e:
            logging.error(f"Failed to compute reference matrix exponential: {e}")
            return False  # Cannot verify if reference fails

        # Compare the proposed solution with the reference solution
        rtol = 1e-5
        atol = 1e-8
        A2 = expA_ref.copy()
        A2.sort_indices()
        A2.eliminate_zeros()
        B2 = solution.copy()
        B2.sort_indices()
        B2.eliminate_zeros()
        are_indices_equal = np.array_equal(A2.indices, B2.indices) and np.array_equal(
            A2.indptr, B2.indptr
        )
        are_data_equal = np.allclose(A2.data, B2.data, rtol=rtol, atol=atol)

        if not are_indices_equal or not are_data_equal:
            logging.error("Proposed matrix exponential is not close enough to the reference value.")

            return False

        return True
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
