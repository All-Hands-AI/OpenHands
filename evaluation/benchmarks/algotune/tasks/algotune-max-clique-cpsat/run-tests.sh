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
PROBLEM_SIZE = 12           # Task difficulty (i.e. "n" in AlgoTune)
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

from typing import Any, List

class Solver:
    def solve(self, problem, **kwargs) -> Any:  # noqa: D401
        """
        Solve the Maximum Clique problem.

        Uses a fast exact branch-and-bound algorithm (Tomita-style) with
        greedy coloring for strong upper bounds and bitset operations for speed.

        :param problem: 2D adjacency matrix (list of lists with 0/1).
        :return: List of node indices forming a maximum clique.
        """
        # Basic validation and trivial cases
        if problem is None:
            return []
        n = len(problem)
        if n == 0:
            return []
        if n == 1:
            return [0]

        # Build degrees and check trivial structures
        deg = [0] * n
        for i, row in enumerate(problem):
            # Count neighbors (ignore self-loops)
            cnt = 0
            for j, v in enumerate(row):
                if i != j and v:
                    cnt += 1
            deg[i] = cnt

        # If graph is complete, return all vertices
        if all(d == n - 1 for d in deg):
            return list(range(n))
        # If no edges, any single vertex is a maximum clique
        if max(deg) == 0:
            return [0]

        # Reorder vertices by non-increasing degree for better pruning
        order = sorted(range(n), key=lambda i: deg[i], reverse=True)
        pos = [0] * n
        for new_idx, old_idx in enumerate(order):
            pos[old_idx] = new_idx

        # Build bitset adjacency in the new indexing
        adj: List[int] = [0] * n
        for new_i, old_i in enumerate(order):
            bits = 0
            row = problem[old_i]
            for old_j, val in enumerate(row):
                if old_j != old_i and val:
                    bits |= 1 << pos[old_j]
            adj[new_i] = bits

        # Helpers
        def popcount(x: int) -> int:
            return x.bit_count()

        def lsb_index(x: int) -> int:
            # Index (0-based) of least significant set bit
            return (x & -x).bit_length() - 1

        # Greedy heuristic for initial lower bound
        def greedy_clique() -> List[int]:
            P = (1 << n) - 1
            if P == 0:
                return []
            # pick vertex with max degree in adj
            max_d = -1
            start = 0
            m = P
            while m:
                v = lsb_index(m)
                m &= m - 1
                d = popcount(adj[v])
                if d > max_d:
                    max_d = d
                    start = v
            clique = [start]
            P &= adj[start]
            while P:
                # pick vertex with most connections within P
                best_v = -1
                best_d = -1
                mm = P
                while mm:
                    v = lsb_index(mm)
                    mm &= mm - 1
                    d = popcount(adj[v] & P)
                    if d > best_d:
                        best_d = d
                        best_v = v
                clique.append(best_v)
                P &= adj[best_v]
            return clique

        best_clique: List[int] = greedy_clique()
        best_size = len(best_clique)

        # Greedy coloring to produce an order and bounds
        def color_sort(P: int) -> tuple[list[int], list[int]]:
            order_: List[int] = []
            bounds_: List[int] = []
            if P == 0:
                return order_, bounds_
            U = P
            color = 0
            while U:
                color += 1
                Q = U
                while Q:
                    v = lsb_index(Q)
                    # remove v from Q
                    Q &= Q - 1
                    # assign color to v
                    order_.append(v)
                    bounds_.append(color)
                    # remove neighbors from Q to keep an independent set
                    Q &= ~adj[v]
                    # mark v as colored
                    U &= ~(1 << v)
            return order_, bounds_

        # Branch and bound
        R_list: List[int] = []

        def expand(P: int) -> None:
            nonlocal best_size, best_clique
            order_, bounds_ = color_sort(P)
            # iterate vertices in reverse (highest color first)
            for idx in range(len(order_) - 1, -1, -1):
                v = order_[idx]
                # Bound pruning
                if len(R_list) + bounds_[idx] <= best_size:
                    return
                # include v
                R_list.append(v)
                P_v = P & adj[v]
                if P_v:
                    expand(P_v)
                else:
                    # maximal clique found
                    if len(R_list) > best_size:
                        best_size = len(R_list)
                        best_clique = R_list.copy()
                # backtrack
                R_list.pop()
                # remove v from P for subsequent iterations
                P &= ~(1 << v)

        all_vertices = (1 << n) - 1
        expand(all_vertices)

        # Map back to original indices and return sorted
        res = [order[v] for v in best_clique]
        res.sort()
        return res
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
