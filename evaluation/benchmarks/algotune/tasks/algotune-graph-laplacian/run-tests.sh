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
PROBLEM_SIZE = 44505           # Task difficulty (i.e. "n" in AlgoTune)
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
import scipy.sparse
import scipy.sparse.csgraph



class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the GraphLaplacian task.

        Computes the Laplacian matrix of a graph, which can be either the standard
        combinatorial Laplacian (L = D - A) or the normalized Laplacian.
        The input graph A is represented in CSR format.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generates a sparse graph and parameters for Laplacian computation.

        Creates a sparse, symmetric graph A of size n x n using a banded structure
        similar to the benchmark code (`spdiags`). Also determines whether to compute
        the standard or normalized Laplacian.

        :param n: The dimension of the square graph matrix A.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the problem with keys:
                 "data": List of non-zero graph weights for CSR format.
                 "indices": List of column indices.
                 "indptr": List of index pointers.
                 "shape": Tuple (n, n).
                 "normed": Boolean flag, True for normalized Laplacian, False for standard.
        """
        logging.debug(f"Generating Graph Laplacian problem with n={n}, random_seed={random_seed}")
        random.seed(random_seed)
        np.random.seed(random_seed)
        rng = np.random.default_rng(random_seed)

        # Create a banded matrix structure (similar to benchmark)
        num_bands = min(9, max(1, n // 10))  # Number of bands on each side
        # Generate random data for the diagonals
        # Need data for num_bands lower diagonals and num_bands upper diagonals
        diag_data = rng.uniform(0.1, 1.0, size=(num_bands, n))  # Positive weights

        # Define diagonal offsets: -num_bands to -1 and 1 to num_bands
        diags = list(range(-num_bands, 0)) + list(range(1, num_bands + 1))
        # Stack data appropriately for spdiags (needs data for each diag)
        spdiags_data = np.vstack((diag_data, diag_data))  # use same data for lower/upper initially

        A_banded = scipy.sparse.spdiags(spdiags_data, diags, n, n, format="coo")

        # Ensure symmetry by taking the elementwise max with its transpose
        A_sym = A_banded.maximum(A_banded.T)

        # Convert to CSR
        graph_csr = A_sym.tocsr()
        graph_csr.eliminate_zeros()  # Clean up explicit zeros

        # Decide whether to compute normalized Laplacian
        normed = random.choice([True, False])

        problem = {
            "data": graph_csr.data.tolist(),
            "indices": graph_csr.indices.tolist(),
            "indptr": graph_csr.indptr.tolist(),
            "shape": graph_csr.shape,
            "normed": normed,
        }
        logging.debug(f"Generated graph with {graph_csr.nnz} edges, normed={normed}.")
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """
        Computes the graph Laplacian using scipy.sparse.csgraph.laplacian.

        The output Laplacian is returned in CSR format components.

        :param problem: A dictionary representing the graph (CSR) and `normed` flag.
        :return: A dictionary with key "laplacian" containing CSR components:
                 "data": List of non-zero Laplacian matrix entries.
                 "indices": List of column indices.
                 "indptr": List of index pointers.
                 "shape": Tuple (n, n).
                 Returns empty dict components on failure.
        """
        try:
            graph_csr = scipy.sparse.csr_matrix(
                (problem["data"], problem["indices"], problem["indptr"]), shape=problem["shape"]
            )
            normed = problem["normed"]
        except Exception as e:
            logging.error(f"Failed to reconstruct input CSR matrix: {e}")
            return {
                "laplacian": {
                    "data": [],
                    "indices": [],
                    "indptr": [],
                    "shape": problem.get("shape", (0, 0)),
                }
            }

        try:
            # Compute the Laplacian
            L = scipy.sparse.csgraph.laplacian(graph_csr, normed=normed)

            # Ensure output is CSR format
            if not isinstance(L, scipy.sparse.csr_matrix):
                L_csr = L.tocsr()
            else:
                L_csr = L
            L_csr.eliminate_zeros()  # Clean up

        except Exception as e:
            logging.error(f"scipy.sparse.csgraph.laplacian failed: {e}")
            return {
                "laplacian": {"data": [], "indices": [], "indptr": [], "shape": problem["shape"]}
            }

        # Return lists to avoid ambiguous truth-value checks downstream
        solution = {
            "laplacian": {
                "data": L_csr.data.tolist(),
                "indices": L_csr.indices.tolist(),
                "indptr": L_csr.indptr.tolist(),
                "shape": L_csr.shape,
            }
        }
        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, dict[str, Any]]) -> bool:
        """
        Check if the provided matrix is the correct graph Laplacian.

        Checks structure, CSR components, and numerical closeness of data values
        to the reference scipy.sparse.csgraph.laplacian output.

        :param problem: The problem definition dictionary.
        :param solution: The proposed solution dictionary containing Laplacian CSR components.
        :return: True if the solution is valid and correct, False otherwise.
        """
        required_keys = ["data", "indices", "indptr", "shape", "normed"]
        if not all(k in problem for k in required_keys):
            logging.error(f"Problem dictionary missing required keys: {required_keys}")
            return False
        normed = problem["normed"]

        # Validate solution structure
        if not isinstance(solution, dict) or "laplacian" not in solution:
            logging.error("Solution format invalid: missing 'laplacian' key.")
            return False
        L_solution_dict = solution["laplacian"]
        if not isinstance(L_solution_dict, dict) or not all(
            k in L_solution_dict for k in ["data", "indices", "indptr", "shape"]
        ):
            logging.error("Solution 'laplacian' dict missing CSR components.")
            return False

        # Handle potential failure case from solve() using size/len-based checks
        data = L_solution_dict["data"]
        indptr = L_solution_dict["indptr"]

        def _is_empty(x):
            if x is None:
                return True
            if isinstance(x, np.ndarray):
                return x.size == 0
            try:
                return len(x) == 0
            except TypeError:
                return False

        # This detects the explicit "failure" payload (both empty lists).
        # Note: a valid empty CSR of shape (n,n) would have data == [] but indptr length == n+1.
        if _is_empty(data) and _is_empty(indptr):
            logging.warning(
                "Proposed solution seems empty (potential failure). Checking reference."
            )
            try:
                graph_csr = scipy.sparse.csr_matrix(
                    (problem["data"], problem["indices"], problem["indptr"]), shape=problem["shape"]
                )
                ref_L = scipy.sparse.csgraph.laplacian(graph_csr, normed=normed)
                if not isinstance(ref_L, scipy.sparse.spmatrix) or ref_L.nnz == 0:
                    # Reference also empty/invalid → accept failure sentinel.
                    logging.info(
                        "Reference solver also produced empty/invalid result. Accepting failure."
                    )
                    return True
                else:
                    logging.error(
                        "Reference solver succeeded, but proposed solution was empty/invalid."
                    )
                    return False
            except Exception:
                logging.info("Reference solver also failed. Accepting empty solution.")
                return True  # Both failed

        # Reconstruct proposed Laplacian from solution
        try:
            proposed_L_csr = scipy.sparse.csr_matrix(
                (L_solution_dict["data"], L_solution_dict["indices"], L_solution_dict["indptr"]),
                shape=L_solution_dict["shape"],
            )
            if proposed_L_csr.shape != problem["shape"]:
                logging.error(
                    f"Proposed Laplacian shape {proposed_L_csr.shape} != problem shape {problem['shape']}."
                )
                return False
        except Exception as e:
            logging.error(f"Failed to reconstruct proposed Laplacian from solution data: {e}")
            return False

        # Compute reference Laplacian
        try:
            graph_csr = scipy.sparse.csr_matrix(
                (problem["data"], problem["indices"], problem["indptr"]), shape=problem["shape"]
            )
            ref_L_raw = scipy.sparse.csgraph.laplacian(graph_csr, normed=normed)
            # Ensure reference is CSR for comparison
            if not isinstance(ref_L_raw, scipy.sparse.csr_matrix):
                ref_L_csr = ref_L_raw.tocsr()
            else:
                ref_L_csr = ref_L_raw
            ref_L_csr.eliminate_zeros()  # Canonical form

        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False  # Cannot verify if reference fails

        # Compare proposed CSR with reference CSR
        # 1. Compare shapes (already done)
        # 2. Compare structure (indices, indptr) - should be identical for canonical CSR
        if not np.array_equal(proposed_L_csr.indices, ref_L_csr.indices) or not np.array_equal(
            proposed_L_csr.indptr, ref_L_csr.indptr
        ):
            logging.error(
                "CSR structure (indices or indptr) of proposed Laplacian does not match reference."
            )
            return False

        # 3. Compare data values with tolerance
        rtol = 1e-5
        atol = 1e-8
        if not np.allclose(proposed_L_csr.data, ref_L_csr.data, rtol=rtol, atol=atol):
            max_diff = (
                np.max(np.abs(proposed_L_csr.data - ref_L_csr.data))
                if len(proposed_L_csr.data) > 0
                else 0
            )
            logging.error(
                "CSR data values of proposed Laplacian do not match reference within tolerance."
            )
            logging.error(f"Max absolute difference in data: {max_diff:.3e}")
            return False

        logging.debug("Solution verification successful.")
        return True
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
