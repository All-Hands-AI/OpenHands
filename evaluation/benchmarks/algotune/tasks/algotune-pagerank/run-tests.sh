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
PROBLEM_SIZE = 4798           # Task difficulty (i.e. "n" in AlgoTune)
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
import numba
from typing import Any, List
import itertools

# This helper function is JIT-compiled by Numba for performance.
# It implements the core PageRank power iteration logic.
@numba.njit(cache=True, fastmath=True)
def _pagerank_numba(
    adj_list_indices: np.ndarray,
    adj_list_indptr: np.ndarray,
    out_degree: np.ndarray,
    n: int,
    alpha: float,
    max_iter: int,
    tol: float,
) -> np.ndarray:
    """
    Calculates PageRank scores using power iteration, accelerated with Numba.

    Args:
        adj_list_indices: CSR-style array of neighbor indices.
        adj_list_indptr: CSR-style array of index pointers.
        out_degree: Array of out-degrees for each node.
        n: Number of nodes in the graph.
        alpha: Damping factor.
        max_iter: Maximum number of iterations.
        tol: Convergence tolerance for L1 norm.

    Returns:
        A numpy array of PageRank scores.
    """
    # Initialize PageRank scores uniformly
    r = np.full(n, 1.0 / n, dtype=np.float64)

    # Identify dangling nodes (nodes with no outgoing links)
    dangling_nodes_mask = out_degree == 0
    
    # Pre-calculate the constant teleportation term
    teleport_val = (1.0 - alpha) / n

    for _ in range(max_iter):
        r_last = r
        r_new = np.zeros(n, dtype=np.float64)

        # 1. Calculate the total rank from dangling nodes
        dangling_rank_sum = 0.0
        # This loop is faster inside numba than np.sum(r_last[dangling_nodes_mask])
        for i in range(n):
            if dangling_nodes_mask[i]:
                dangling_rank_sum += r_last[i]
        
        # Distribute dangling rank and teleportation probability to all nodes
        dangling_and_teleport = alpha * (dangling_rank_sum / n) + teleport_val
        r_new += dangling_and_teleport

        # 2. Distribute rank from non-dangling nodes
        for i in range(n):
            if not dangling_nodes_mask[i]:
                # Distribute this node's rank to its neighbors
                start = adj_list_indptr[i]
                end = adj_list_indptr[i + 1]
                rank_to_distribute = alpha * r_last[i] / out_degree[i]
                for k in range(start, end):
                    j = adj_list_indices[k]
                    r_new[j] += rank_to_distribute
        
        r = r_new

        # 3. Check for convergence using L1 norm
        err = 0.0
        for i in range(n):
            err += abs(r[i] - r_last[i])
        
        if err < n * tol: # Scale tolerance by n as in networkx
            break
            
    return r

class Solver:
    """
    A solver for the PageRank problem that uses a Numba-accelerated
    power iteration method for high performance.
    """
    def __init__(self):
        """Initializes the solver with default PageRank parameters."""
        self.alpha = 0.85
        self.max_iter = 100
        self.tol = 1.0e-6 # networkx default tolerance

    def solve(self, problem: dict[str, List[List[int]]], **kwargs) -> dict[str, Any]:
        """
        Calculates PageRank scores for a given graph.

        Args:
            problem: A dictionary containing the adjacency list of the graph.
            **kwargs: Can be used to override default parameters like alpha, max_iter, tol.

        Returns:
            A dictionary with the key "pagerank_scores" and a list of scores.
        """
        adj_list = problem["adjacency_list"]
        n = len(adj_list)

        if n == 0:
            return {"pagerank_scores": []}
        if n == 1:
            return {"pagerank_scores": [1.0]}

        # Override parameters if provided in kwargs
        alpha = kwargs.get("alpha", self.alpha)
        max_iter = kwargs.get("max_iter", self.max_iter)
        tol = kwargs.get("tol", self.tol)

        # Optimized conversion of adjacency list to CSR-like format
        
        # Calculate out_degrees (lengths of neighbor lists)
        out_degree = np.array([len(neighbors) for neighbors in adj_list], dtype=np.int32)

        # Efficiently create indptr using cumsum
        indptr = np.empty(n + 1, dtype=np.int32)
        indptr[0] = 0
        np.cumsum(out_degree, out=indptr[1:])

        # Efficiently create indices by flattening the adjacency list
        num_edges = indptr[-1]
        indices = np.fromiter(itertools.chain.from_iterable(adj_list), 
                              dtype=np.int32, 
                              count=num_edges)

        # Call the Numba-jitted function to perform the calculation
        pagerank_scores_np = _pagerank_numba(
            indices, indptr, out_degree, n, alpha, max_iter, tol
        )

        return {"pagerank_scores": pagerank_scores_np.tolist()}
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
