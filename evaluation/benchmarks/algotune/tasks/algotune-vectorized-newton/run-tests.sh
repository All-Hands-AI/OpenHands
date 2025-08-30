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
PROBLEM_SIZE = 710026           # Task difficulty (i.e. "n" in AlgoTune)
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
import logging
import random

import numpy as np
import scipy.optimize
import numbers



# Define the vectorized function and derivative used in the benchmark
def _task_f_vec(x, *a):
    # Ensure x is treated as numpy array for vectorization
    x = np.asarray(x)
    # a contains (a0, a1, a2, a3, a4, a5) where a0, a1 can be arrays
    a0, a1, a2, a3, a4, a5 = a
    b = a0 + x * a3  # b will be array if a0 or x is array
    term1 = a2 * (np.exp(b / a5) - 1.0)
    term2 = b / a4
    return a1 - term1 - term2 - x


def _task_f_vec_prime(x, *a):
    x = np.asarray(x)
    a0, a1, a2, a3, a4, a5 = a
    b_deriv_term = a3 / a5
    exp_term = np.exp((a0 + x * a3) / a5)
    return -a2 * exp_term * b_deriv_term - a3 / a4 - 1.0


class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the VectorizedNewton task.

        Finds roots for `n` instances of a parameterized function simultaneously
        using a vectorized call to `scipy.optimize.newton` (Newton-Raphson).
        The function `f(x, *params)` and its derivative `fprime(x, *params)`
        are evaluated element-wise over arrays of initial guesses `x0` and
        corresponding parameter arrays `a0`, `a1`.
        """
        super().__init__(**kwargs)
        self.func = _task_f_vec
        self.fprime = _task_f_vec_prime
        # Fixed parameters from benchmark, except a0, a1 which scale with n
        self.a2 = 1e-09
        self.a3 = 0.004
        self.a4 = 10.0
        self.a5 = 0.27456

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, list[float]]:
        """
        Generates `n` initial guesses `x0` and corresponding parameter arrays `a0`, `a1`.

        Uses the specific function structure from the `NewtonArray` benchmark.

        :param n: The number of simultaneous root-finding problems (size of arrays).
        :param random_seed: Seed for reproducibility.
        :return: A dictionary with keys:
                 "x0": List of `n` initial guesses.
                 "a0": List of `n` corresponding 'a0' parameter values.
                 "a1": List of `n` corresponding 'a1' parameter values.
        """
        logging.debug(f"Generating Vectorized Newton problem with n={n}, random_seed={random_seed}")
        random.seed(random_seed)
        np.random.seed(random_seed)
        rng = np.random.default_rng(random_seed)

        # Generate arrays based on benchmark example structure
        x0 = rng.uniform(6.0, 8.0, size=n).tolist()  # Around the expected root area
        # Generate a0 similar to example
        a0 = rng.uniform(1.0, 6.0, size=n)
        a0[::10] = rng.uniform(5.0, 5.5, size=len(a0[::10]))  # Add some variation
        a0 = a0.tolist()
        # Generate a1 similar to example
        a1 = (np.sin(rng.uniform(0, 2 * np.pi, size=n)) + 1.0) * 7.0
        a1 = a1.tolist()

        problem = {"x0": x0, "a0": a0, "a1": a1}
        logging.debug(f"Generated {n} vectorized problem instances.")
        return problem

    def solve(self, problem: dict[str, list[float]]) -> dict[str, list[float]]:
        """
        Finds roots using a single vectorized call to scipy.optimize.newton.

        :param problem: Dict with lists "x0", "a0", "a1".
        :return: Dictionary with key "roots": List of `n` found roots. Uses NaN on failure.
        """
        try:
            x0_arr = np.array(problem["x0"])
            a0_arr = np.array(problem["a0"])
            a1_arr = np.array(problem["a1"])
            n = len(x0_arr)
            if len(a0_arr) != n or len(a1_arr) != n:
                raise ValueError("Input arrays have mismatched lengths")
        except Exception as e:
            logging.error(f"Failed to reconstruct input arrays: {e}")
            # Cannot determine n reliably, return empty list?
            return {"roots": []}

        # Assemble args tuple for vectorized function
        args = (a0_arr, a1_arr, self.a2, self.a3, self.a4, self.a5)

        roots_list = []
        try:
            # Perform vectorized call
            roots_arr = scipy.optimize.newton(self.func, x0_arr, fprime=self.fprime, args=args)
            roots_list = roots_arr
            # Check if newton returned a scalar unexpectedly (e.g., if n=1)
            if np.isscalar(roots_list):
                roots_list = np.array([roots_list])

            # Pad with NaN if output length doesn't match input (shouldn't happen with vectorization)
            if len(roots_list) != n:
                logging.warning(
                    f"Vectorized Newton output length {len(roots_list)} != input {n}. Padding with NaN."
                )
                roots_list.extend([float("nan")] * (n - len(roots_list)))

        except RuntimeError as e:
            # Vectorized call might fail entirely or partially? SciPy docs are unclear.
            # Assume it raises error if *any* fail to converge. Return all NaNs.
            logging.warning(
                f"Vectorized Newton failed to converge (may affect all elements): {e}. Returning NaNs."
            )
            roots_list = [float("nan")] * n
        except Exception as e:
            logging.error(f"Unexpected error in vectorized Newton: {e}. Returning NaNs.")
            roots_list = [float("nan")] * n

        solution = {"roots": roots_list}
        return solution

    def is_solution(
        self, problem: dict[str, list[float]], solution: dict[str, list[float]]
    ) -> bool:
        """
        Check if the provided roots are correct for the vectorized problem.

        - Accepts list/tuple/np.ndarray or a numeric scalar (including NumPy scalars).
        - Compares element-wise to the reference vectorized output with tolerances.
        - Optionally warns if |f(root)| is not small.
        """
        required_keys = ["x0", "a0", "a1"]
        if not all(k in problem for k in required_keys):
            logging.error(f"Problem dictionary missing required keys: {required_keys}")
            return False

        try:
            n = len(problem["x0"])
        except Exception:
            logging.error("Cannot determine problem size n from input.")
            return False

        if not isinstance(solution, dict) or "roots" not in solution:
            logging.error("Solution format invalid: missing 'roots' key.")
            return False

        proposed_roots = solution["roots"]

        # Normalize proposed_roots to a 1D float array
        try:
            if isinstance(proposed_roots, numbers.Real):
                proposed_arr = np.array([proposed_roots], dtype=float)
            else:
                proposed_arr = np.asarray(proposed_roots, dtype=float).reshape(-1)
        except Exception as e:
            logging.error(f"Could not interpret 'roots' as numeric array: {e}")
            return False

        if proposed_arr.shape[0] != n:
            logging.error(f"'roots' length mismatch ({proposed_arr.shape[0]} != {n}).")
            return False

        # Recompute reference solution and normalize it too
        ref_solution = self.solve(problem)
        if not isinstance(ref_solution, dict) or "roots" not in ref_solution:
            logging.error("Internal error: reference solution missing 'roots'.")
            return False

        try:
            ref_arr = np.asarray(ref_solution["roots"], dtype=float).reshape(-1)
        except Exception as e:
            logging.error(f"Internal error: could not interpret reference roots: {e}")
            return False

        if ref_arr.shape[0] != n:
            logging.error(
                f"Internal error: reference length {ref_arr.shape[0]} != expected {n}."
            )
            return False

        rtol = 1e-5
        atol = 1e-7
        is_close = np.allclose(proposed_arr, ref_arr, rtol=rtol, atol=atol, equal_nan=True)
        if not is_close:
            logging.error("Proposed roots do not match reference roots within tolerance.")
            mism = ~np.isclose(proposed_arr, ref_arr, rtol=rtol, atol=atol, equal_nan=True)
            num_mismatch = int(np.sum(mism))
            logging.error(f"Number of mismatches: {num_mismatch} / {n}")
            # Log up to 5 mismatches
            bad_idxs = np.flatnonzero(mism)[:5]
            for i in bad_idxs:
                logging.error(f"Mismatch at index {i}: Proposed={proposed_arr[i]}, Ref={ref_arr[i]}")
            return False

        # Optional: Basic validity check f(root) ~= 0 (warn-only, as before)
        func_tol = 1e-8
        try:
            finite_mask = np.isfinite(proposed_arr)
            if np.any(finite_mask):
                a0_arr = np.asarray(problem["a0"], dtype=float)[finite_mask]
                a1_arr = np.asarray(problem["a1"], dtype=float)[finite_mask]
                args_check = (a0_arr, a1_arr, self.a2, self.a3, self.a4, self.a5)
                f_vals = self.func(proposed_arr[finite_mask], *args_check)
                max_abs_f = float(np.max(np.abs(f_vals))) if f_vals.size else 0.0
                if np.any(np.abs(f_vals) > func_tol * 10):
                    bad_indices = np.where(np.abs(f_vals) > func_tol * 10)[0]
                    logging.warning(
                        f"Some roots ({len(bad_indices)}) do not satisfy |f(root)| <= {func_tol * 10}. "
                        f"Max |f(root)| = {max_abs_f}"
                    )
        except Exception as e:
            logging.warning(f"Could not perform basic validity check |f(root)|~0 due to error: {e}")

        logging.debug("Solution verification successful.")
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
pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
