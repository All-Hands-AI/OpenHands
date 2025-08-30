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
PROBLEM_SIZE = 61           # Task difficulty (i.e. "n" in AlgoTune)
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
from typing import Any, Dict, List
import time
import sys
import math
from fractions import Fraction
from ortools.sat.python import cp_model

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> List[int]:
        """
        Maximum Weighted Independent Set (MWIS).

        Strategy:
        - For n <= bb_threshold run a branch-and-bound on bitsets by finding
          a maximum-weight clique in the complement graph. Uses vertex
          permutation so high-weight vertices get low bit indices (LSB-first),
          greedy coloring for upper bounds, and LSB iteration to avoid scanning.
        - For larger graphs, fall back to OR-Tools CP-SAT.

        Optional kwargs:
            - time_limit: float seconds to limit B&B search (will return best found).
            - num_workers: int number of CP-SAT workers for fallback.
            - bb_threshold: int to override branching threshold (default 70).
        """
        adj = problem.get("adj_matrix", [])
        weights = problem.get("weights", [])
        n = len(weights)
        if n == 0:
            return []

        # Parse time limit
        time_limit = kwargs.get("time_limit", None)
        try:
            time_limit = float(time_limit) if time_limit is not None else None
        except Exception:
            time_limit = None
        start_time = time.time()

        # Convert weights to floats for B&B
        w_float: List[float] = []
        for w in weights:
            try:
                w_float.append(float(w))
            except Exception:
                w_float.append(float(str(w)))

        # Prepare integer weights for CP-SAT fallback
        all_int = all(abs(w - round(w)) < 1e-12 for w in w_float)
        if all_int:
            w_int = [int(round(w)) for w in w_float]
        else:
            try:
                fracs = [Fraction(str(w)).limit_denominator(10**6) for w in weights]
                denom = 1
                for f in fracs:
                    denom = denom * f.denominator // math.gcd(denom, f.denominator)
                    if denom > 1_000_000:
                        denom = 1000
                        break
                w_int = [int(f * denom) for f in fracs]
            except Exception:
                w_int = [int(round(w * 1000)) for w in w_float]

        # Branch-and-bound threshold
        bb_threshold = kwargs.get("bb_threshold", 70)
        try:
            bb_threshold = int(bb_threshold)
        except Exception:
            bb_threshold = 70

        # For large graphs, use CP-SAT fallback to avoid exponential search
        if n > bb_threshold:
            model = cp_model.CpModel()
            nodes = [model.NewBoolVar(f"x_{i}") for i in range(n)]
            for i in range(n):
                row = adj[i] if i < len(adj) else [0] * n
                for j in range(i + 1, n):
                    val = row[j] if j < len(row) else 0
                    if val:
                        model.Add(nodes[i] + nodes[j] <= 1)
            model.Maximize(sum(w_int[i] * nodes[i] for i in range(n)))
            solver = cp_model.CpSolver()
            if time_limit is not None:
                try:
                    solver.parameters.max_time_in_seconds = float(time_limit)
                except Exception:
                    pass
            workers = kwargs.get("num_workers", 8)
            try:
                solver.parameters.num_search_workers = int(workers)
            except Exception:
                pass
            status = solver.Solve(model)
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                res = [i for i in range(n) if solver.Value(nodes[i]) == 1]
                res.sort()
                return res
            return []

        # Build original adjacency masks (handle ragged rows)
        full_mask = (1 << n) - 1
        orig_adj_mask = [0] * n
        for i in range(n):
            row = adj[i] if i < len(adj) else [0] * n
            m = 0
            for j in range(min(len(row), n)):
                if row[j]:
                    m |= (1 << j)
            orig_adj_mask[i] = m

        # Quick trivial case: no edges -> take all positive-weight nodes
        if all(m == 0 for m in orig_adj_mask):
            res = [i for i, w in enumerate(w_float) if w > 0]
            res.sort()
            return res

        # Complement graph adjacency (we search maximum-weight clique here)
        comp_adj = [0] * n
        for i in range(n):
            comp_adj[i] = (~orig_adj_mask[i]) & full_mask & ~(1 << i)

        # Heuristic ordering: descending weight, tie-break by complement degree
        comp_deg = [comp_adj[i].bit_count() for i in range(n)]
        order_by_weight = sorted(range(n), key=lambda v: (w_float[v], comp_deg[v]), reverse=True)

        # Permute vertices so high-weight vertices have low indices (LSB-first)
        perm = order_by_weight[:]  # new_index -> old_index
        inv = [0] * n  # old_index -> new_index
        for newpos, old in enumerate(perm):
            inv[old] = newpos

        # Permute complement adjacency masks into new indices
        comp_adj_perm = [0] * n
        for old in range(n):
            newpos = inv[old]
            m = comp_adj[old]
            nm = 0
            while m:
                lsb = m & -m
                j = lsb.bit_length() - 1
                nm |= (1 << inv[j])
                m ^= lsb
            comp_adj_perm[newpos] = nm

        # Permute weights
        w_local = [0.0] * n
        for old in range(n):
            w_local[inv[old]] = w_float[old]

        # Bound cache for coloring
        bound_cache: Dict[int, float] = {}

        comp_adj_local = comp_adj_perm
        FULL = (1 << n) - 1
        EPS = 1e-12

        def color_bound(mask: int) -> float:
            """Greedy coloring bound: sum of max weights per color (independent sets)."""
            if mask == 0:
                return 0.0
            if mask in bound_cache:
                return bound_cache[mask]
            color_masks: List[int] = []
            color_max: List[float] = []
            m = mask
            # iterate vertices in increasing index order (which is descending weight)
            while m:
                lsb = m & -m
                v = lsb.bit_length() - 1
                m ^= lsb
                av = comp_adj_local[v]
                placed = False
                for idx, cmask in enumerate(color_masks):
                    # can place v in this color if it has no edges to members (independent)
                    if (av & cmask) == 0:
                        color_masks[idx] = cmask | (1 << v)
                        if w_local[v] > color_max[idx]:
                            color_max[idx] = w_local[v]
                        placed = True
                        break
                if not placed:
                    color_masks.append(1 << v)
                    color_max.append(w_local[v])
            ub = sum(color_max)
            bound_cache[mask] = ub
            return ub

        # Greedy initial clique (warm start) - only take positive weight vertices
        def greedy_initial():
            mask = FULL
            chosen = 0
            total = 0.0
            while mask:
                lsb = mask & -mask
                v = lsb.bit_length() - 1
                # choose only if positive weight
                if w_local[v] > 0:
                    chosen |= (1 << v)
                    total += w_local[v]
                    mask &= comp_adj_local[v]
                else:
                    # skip v
                    mask ^= (1 << v)
            return chosen, total

        best_mask = 0
        best_weight = 0.0  # allow empty set as valid solution with weight 0
        gm, gw = greedy_initial()
        if gw > best_weight:
            best_weight = gw
            best_mask = gm

        sys.setrecursionlimit(10000)

        # Main recursive expansion using LSB iteration
        def expand(mask: int, cur_weight: float, cur_mask: int):
            nonlocal best_weight, best_mask
            # Respect time limit if provided
            if time_limit is not None and (time.time() - start_time) > time_limit:
                return
            ub = cur_weight + color_bound(mask)
            if ub <= best_weight + EPS:
                return
            sub = mask
            # iterate candidates LSB-first (highest priority first due to permutation)
            while sub:
                lsb = sub & -sub
                v = lsb.bit_length() - 1
                sub ^= lsb
                mv = 1 << v
                new_mask = mask & comp_adj_local[v]
                new_weight = cur_weight + w_local[v]
                if new_weight + color_bound(new_mask) > best_weight + EPS:
                    if new_mask == 0:
                        if new_weight > best_weight + EPS:
                            best_weight = new_weight
                            best_mask = cur_mask | mv
                    else:
                        expand(new_mask, new_weight, cur_mask | mv)
                # exclude v from mask for remaining iterations and pruning
                mask ^= mv
                if cur_weight + color_bound(mask) <= best_weight + EPS:
                    return

        expand(FULL, 0.0, 0)

        # Map best_mask (permuted indices) back to original indices
        result = [perm[i] for i in range(n) if (best_mask >> i) & 1]
        result.sort()
        return result
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
