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
PROBLEM_SIZE = 9           # Task difficulty (i.e. "n" in AlgoTune)
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
from typing import List, Any

class Solver:
    """
    Exact branch-and-bound solver for the Minimum Dominating Set problem.
    Uses bitmask representations, dominated-candidate reduction, greedy initial
    solution and pruning with a simple lower bound and memoization.
    """

    def solve(self, problem: List[List[int]], **kwargs) -> Any:
        n = len(problem)
        if n == 0:
            return []

        # Build closed-neighborhood masks Nmask[i] = bitmask of {i} union neighbors(i)
        Nmask = [0] * n
        for i in range(n):
            mask = 1 << i
            row = problem[i]
            for j, val in enumerate(row):
                if val:
                    mask |= 1 << j
            Nmask[i] = mask

        all_mask = (1 << n) - 1

        # Remove dominated candidate vertices: if Nmask[i] is subset of Nmask[j] (i != j),
        # then i is never needed as a dominator (j is at least as powerful).
        keep = [True] * n
        for i in range(n):
            if not keep[i]:
                continue
            mi = Nmask[i]
            for j in range(n):
                if i == j or not keep[j]:
                    continue
                mj = Nmask[j]
                if (mi | mj) == mj:
                    keep[i] = False
                    break

        dominators = [i for i in range(n) if keep[i]]
        if not dominators:
            dominators = list(range(n))

        # Precompute candidate dominators for each vertex u:
        candidate_dominators = [[] for _ in range(n)]
        for u in range(n):
            for v in dominators:
                if (Nmask[v] >> u) & 1:
                    candidate_dominators[u].append(v)

        # popcount helper (fast on modern Python)
        if hasattr(int, "bit_count"):
            popcount = lambda x: x.bit_count()
        else:
            popcount = lambda x: bin(x).count("1")

        # Greedy initial solution (upper bound)
        dom = 0
        greedy_sel: List[int] = []
        while dom != all_mask:
            best_v = -1
            best_gain = -1
            for v in dominators:
                gain = popcount(Nmask[v] & ~dom)
                if gain > best_gain:
                    best_gain = gain
                    best_v = v
            if best_gain <= 0:
                break
            greedy_sel.append(best_v)
            dom |= Nmask[best_v]

        best_size = len(greedy_sel) if greedy_sel else n
        best_solution = greedy_sel.copy() if greedy_sel else list(range(n))

        # Memoization: best known count for a dominated-mask
        visited = {}

        # Precompute candidate lengths for quick access
        cand_len = [len(candidate_dominators[u]) for u in range(n)]

        # Depth-first search with pruning
        def dfs(dom_mask: int, count: int, cur_sel: List[int]):
            nonlocal best_size, best_solution

            if count >= best_size:
                return

            if dom_mask == all_mask:
                best_size = count
                best_solution = cur_sel.copy()
                return

            prev = visited.get(dom_mask)
            if prev is not None and prev <= count:
                return
            visited[dom_mask] = count

            rem_mask = all_mask & ~dom_mask
            rem = popcount(rem_mask)

            # Compute simple lower bound: remaining nodes / best possible coverage
            best_cover = 0
            for v in dominators:
                c = popcount(Nmask[v] & rem_mask)
                if c > best_cover:
                    best_cover = c
            if best_cover == 0:
                return
            lb = (rem + best_cover - 1) // best_cover
            if count + lb >= best_size:
                return

            # Choose an undominated vertex u with smallest number of candidates (least branching)
            best_u = -1
            best_candidates = 10 ** 9
            for u in range(n):
                if ((rem_mask >> u) & 1) == 0:
                    continue
                l = cand_len[u]
                if l < best_candidates:
                    best_candidates = l
                    best_u = u
                    if l <= 2:
                        break

            if best_u == -1:
                return

            # Candidate dominators for best_u, order by coverage (descending) to find good solutions early
            cand = candidate_dominators[best_u]
            cand_sorted = sorted(cand, key=lambda v: -popcount(Nmask[v] & rem_mask))

            for v in cand_sorted:
                new_mask = dom_mask | Nmask[v]
                cur_sel.append(v)
                dfs(new_mask, count + 1, cur_sel)
                cur_sel.pop()
                if count + 1 >= best_size:
                    break

        dfs(0, 0, [])

        # Final safety: ensure result dominates all vertices; otherwise fallback to greedy
        final = sorted(set(best_solution))
        mask_check = 0
        for v in final:
            mask_check |= Nmask[v]
        if mask_check != all_mask:
            final = sorted(set(greedy_sel))

        return final
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
