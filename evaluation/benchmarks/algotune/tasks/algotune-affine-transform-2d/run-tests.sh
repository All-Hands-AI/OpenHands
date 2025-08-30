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
PROBLEM_SIZE = 1123           # Task difficulty (i.e. "n" in AlgoTune)
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
from typing import Any

import numpy as np
import scipy.ndimage



def _is_empty(x):
    if x is None:
        return True
    if isinstance(x, np.ndarray):
        return x.size == 0
    try:
        return len(x) == 0
    except TypeError:
        return False


class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the AffineTransform2D task.

        Performs an affine transformation on a 2D image using scipy.ndimage.affine_transform.
        The transformation is defined by a 2x3 matrix. Uses cubic spline interpolation
        (order=3) and 'constant' mode for handling boundaries.
        """
        super().__init__(**kwargs)
        self.order = 3
        self.mode = "constant"  # Or 'nearest', 'reflect', 'mirror', 'wrap'

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generates a 2D affine transformation problem.

        Creates a random 2D array (image) of size n x n and a 2x3 affine
        transformation matrix.

        :param n: The side dimension of the square input image.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the problem with keys:
                 "image": Input image as a numpy array (n x n).
                 "matrix": The 2x3 affine transformation matrix (numpy array).
        """
        logging.debug(
            f"Generating 2D Affine Transform problem with n={n}, random_seed={random_seed}"
        )
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Generate random n x n image
        image = np.random.rand(n, n) * 255.0  # Example: 0-255 range image

        # Generate a random affine matrix (e.g., combining rotation, scale, shear, translation)
        angle = np.random.uniform(-np.pi / 6, np.pi / 6)  # +/- 30 degrees
        scale = np.random.uniform(0.8, 1.2, size=2)
        shear = np.random.uniform(-0.2, 0.2)
        translation = np.random.uniform(-n * 0.1, n * 0.1, size=2)  # Translate up to 10%

        # Rotation matrix
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        R = np.array([[cos_a, -sin_a], [sin_a, cos_a]])

        # Scale matrix
        S = np.array([[scale[0], 0], [0, scale[1]]])

        # Shear matrix
        H = np.array([[1, shear], [0, 1]])

        # Combine transformations (excluding translation for the 2x2 part)
        M_2x2 = R @ S @ H

        # Create the 2x3 matrix [ M_2x2 | translation ]
        matrix = np.hstack((M_2x2, translation[:, np.newaxis]))

        problem = {"image": image, "matrix": matrix}
        logging.debug(f"Generated 2D Affine Transform problem for image shape ({n},{n})")
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solves the 2D affine transformation problem using scipy.ndimage.affine_transform.

        :param problem: A dictionary representing the problem.
        :return: A dictionary with key "transformed_image":
                 "transformed_image": The transformed image as an array.
        """
        image = problem["image"]
        matrix = problem["matrix"]

        # Perform affine transformation
        try:
            # output_shape can be specified, default is same as input
            transformed_image = scipy.ndimage.affine_transform(
                image, matrix, order=self.order, mode=self.mode
            )
        except Exception as e:
            logging.error(f"scipy.ndimage.affine_transform failed: {e}")
            # Return an empty list to indicate failure? Adjust based on benchmark policy.
            return {"transformed_image": []}

        solution = {"transformed_image": transformed_image}
        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Check if the provided affine transformation solution is valid.

        Checks structure, dimensions, finite values, and numerical closeness to
        the reference scipy.ndimage.affine_transform output.

        :param problem: The problem definition dictionary.
        :param solution: The proposed solution dictionary.
        :return: True if the solution is valid, False otherwise.
        """
        if not all(k in problem for k in ["image", "matrix"]):
            logging.error("Problem dictionary missing 'image' or 'matrix'.")
            return False
        image = problem["image"]
        matrix = problem["matrix"]

        if not isinstance(solution, dict) or "transformed_image" not in solution:
            logging.error("Solution format invalid: missing 'transformed_image' key.")
            return False

        proposed_list = solution["transformed_image"]

        # Handle potential failure case from solve()
        if _is_empty(proposed_list):
            logging.warning("Proposed solution is empty list (potential failure).")
            # Check if reference solver also fails/produces empty-like result
            try:
                ref_output = scipy.ndimage.affine_transform(
                    image, matrix, order=self.order, mode=self.mode
                )
                if ref_output.size == 0:  # Check if reference is also effectively empty
                    logging.info(
                        "Reference solver also produced empty result. Accepting empty solution."
                    )
                    return True
                else:
                    logging.error("Reference solver succeeded, but proposed solution was empty.")
                    return False
            except Exception:
                logging.info("Reference solver also failed. Accepting empty solution.")
                return True  # Both failed, likely invalid input

        if not isinstance(proposed_list, list):
            logging.error("'transformed_image' is not a list.")
            return False

        try:
            proposed_array = np.asarray(proposed_list, dtype=float)
        except ValueError:
            logging.error("Could not convert 'transformed_image' list to numpy float array.")
            return False

        # Expected output shape is usually same as input for affine_transform unless specified
        if proposed_array.shape != image.shape:
            logging.error(f"Output shape {proposed_array.shape} != input shape {image.shape}.")
            # This might be acceptable if output_shape was used, but base case expects same shape.
            # Adjust if the task allows different output shapes.
            return False  # Assuming same shape output for now

        if not np.all(np.isfinite(proposed_array)):
            logging.error("Proposed 'transformed_image' contains non-finite values.")
            return False

        # Re-compute reference solution
        try:
            ref_array = scipy.ndimage.affine_transform(
                image, matrix, order=self.order, mode=self.mode
            )
        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False  # Cannot verify if reference fails

        # Compare results
        rtol = 1e-5
        atol = 1e-7  # Slightly tighter atol for image data often in 0-255 range
        is_close = np.allclose(proposed_array, ref_array, rtol=rtol, atol=atol)

        if not is_close:
            abs_diff = np.abs(proposed_array - ref_array)
            max_abs_err = np.max(abs_diff) if abs_diff.size > 0 else 0
            logging.error(
                f"Solution verification failed: Output mismatch. "
                f"Max absolute error: {max_abs_err:.3f} (rtol={rtol}, atol={atol})"
            )
            return False

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
