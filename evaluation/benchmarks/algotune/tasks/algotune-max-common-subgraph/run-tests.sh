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
PROBLEM_SIZE = 4           # Task difficulty (i.e. "n" in AlgoTune)
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
from typing import Any, List, Tuple

class Solver:
    def solve(self, problem, **kwargs) -> Any:
        A: List[List[int]] = problem["A"]
        B: List[List[int]] = problem["B"]
        n = len(A)
        m = len(B)
        if n == 0 or m == 0:
            return []

        # Build association (modular product) graph using bitsets
        adj, N = self._build_product_graph_bitset(A, B)
        if N == 0:
            return []

        # Maximum clique on association graph
        best_vertices = self._max_clique_bitset(adj)

        # Convert vertex ids back to (i, p)
        res = [(v // m, v % m) for v in best_vertices]
        return res

    @staticmethod
    def _build_product_graph_bitset(
        A: List[List[int]],
        B: List[List[int]],
    ) -> Tuple[List[int], int]:
        n = len(A)
        m = len(B)
        N = n * m
        if N == 0:
            return [], 0

        # Precompute bit masks for B edges and non-edges for each p
        full_m_mask = (1 << m) - 1
        B_edges_mask = [0] * m
        for p in range(m):
            row = B[p]
            mask = 0
            # build bitset of neighbors (excluding self)
            for q in range(m):
                if q != p and row[q]:
                    mask |= 1 << q
            B_edges_mask[p] = mask
        B_nonedges_mask = [0] * m
        for p in range(m):
            # non-edges: all except edges and self
            B_nonedges_mask[p] = (full_m_mask ^ B_edges_mask[p]) & ~(1 << p)

        # Precompute block replicators for each i over j != i
        # R_edge[i] has 1 at bit position j*m if A[i][j] == 1
        # R_non[i] has 1 at bit position j*m if A[i][j] == 0 and j != i
        block_shift = [1 << (j * m) for j in range(n)]
        R_edge = [0] * n
        R_non = [0] * n
        for i in range(n):
            ri_e = 0
            ri_n = 0
            Ai = A[i]
            for j in range(n):
                if j == i:
                    continue
                if Ai[j]:
                    ri_e |= block_shift[j]
                else:
                    ri_n |= block_shift[j]
            R_edge[i] = ri_e
            R_non[i] = ri_n

        # Build adjacency bitset for each vertex (i, p) -> index v = i*m + p
        adj = [0] * N
        Bedges = B_edges_mask
        Bnon = B_nonedges_mask
        for i in range(n):
            base_i = i * m
            ri_e = R_edge[i]
            ri_n = R_non[i]
            for p in range(m):
                v = base_i + p
                bedge = Bedges[p]
                bnon = Bnon[p]
                # neighbors = OR over j!=i of (Ai[j]? bedge << j*m : bnon << j*m)
                # Using block replicators to aggregate in O(1) big-int ops
                neighbors = bedge * ri_e + bnon * ri_n
                adj[v] = neighbors
        return adj, N

    @staticmethod
    def _max_clique_bitset(adj: List[int]) -> List[int]:
        N = len(adj)
        if N == 0:
            return []

        # Initial candidate set: all vertices
        P0 = (1 << N) - 1

        # Greedy heuristic to get an initial lower bound
        def greedy_clique(Pmask: int) -> Tuple[int, int]:
            clique_mask = 0
            size = 0
            P = Pmask
            while P:
                # pick vertex with maximum degree within current P
                best_v = -1
                best_deg = -1
                Q = P
                while Q:
                    lb = Q & -Q
                    v = lb.bit_length() - 1
                    d = (adj[v] & P).bit_count()
                    if d > best_deg:
                        best_deg = d
                        best_v = v
                    Q &= Q - 1
                if best_v < 0:
                    break
                vb = 1 << best_v
                clique_mask |= vb
                size += 1
                P &= adj[best_v]
            return size, clique_mask

        init_size, init_mask = greedy_clique(P0)
        best_size = init_size
        best_mask = init_mask

        # Tomita-style branch and bound with coloring
        adj_loc = adj  # local ref
        bit_count = int.bit_count

        def color_sort(Pmask: int) -> Tuple[List[int], List[int]]:
            # Returns (order, ubounds) where ubounds[i] is the color (upper bound)
            # assigned to order[i]. Colors increase along the order.
            order: List[int] = []
            ubounds: List[int] = []
            color = 0
            P = Pmask
            while P:
                color += 1
                Q = P
                assigned = 0
                while Q:
                    lb = Q & -Q
                    v = lb.bit_length() - 1
                    order.append(v)
                    ubounds.append(color)
                    assigned |= (1 << v)
                    # Remove v and all its neighbors from Q for this color class
                    Q &= ~adj_loc[v]
                    Q &= ~lb
                # Remove all vertices assigned this color from remaining P
                P &= ~assigned
            return order, ubounds

        # Recursive expansion
        def expand(Pmask: int, current_mask: int, rsize: int) -> None:
            nonlocal best_size, best_mask
            if Pmask == 0:
                if rsize > best_size:
                    best_size = rsize
                    best_mask = current_mask
                return

            order, ub = color_sort(Pmask)

            # Iterate in reverse order for effective pruning
            for idx in range(len(order) - 1, -1, -1):
                v = order[idx]
                vb = 1 << v
                if (Pmask & vb) == 0:
                    continue
                if rsize + ub[idx] <= best_size:
                    return
                Nv = Pmask & adj_loc[v]
                # Optional quick bound
                if rsize + 1 + bit_count(Nv) <= best_size:
                    Pmask &= ~vb
                    continue
                expand(Nv, current_mask | vb, rsize + 1)
                Pmask &= ~vb
                # Another bound: even selecting all remaining cannot beat best
                if rsize + bit_count(Pmask) <= best_size:
                    return

        expand(P0, 0, 0)

        # Extract list of vertices from best_mask
        res: List[int] = []
        M = best_mask
        while M:
            lb = M & -M
            v = lb.bit_length() - 1
            res.append(v)
            M &= M - 1
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
