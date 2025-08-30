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
from __future__ import annotations

from typing import Any, List, Tuple

import numpy as np
from ortools.sat.python import cp_model

class Solver:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _segments_rows(obs: np.ndarray) -> tuple[np.ndarray, list[list[tuple[int, int]]]]:
        n, m = obs.shape
        seg_id = -np.ones((n, m), dtype=np.int32)
        segments: list[list[tuple[int, int]]] = []
        sid = 0
        for r in range(n):
            c = 0
            while c < m:
                while c < m and obs[r, c]:
                    c += 1
                if c >= m:
                    break
                cells: list[tuple[int, int]] = []
                while c < m and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    c += 1
                segments.append(cells)
                sid += 1
        return seg_id, segments

    @staticmethod
    def _segments_cols(obs: np.ndarray) -> tuple[np.ndarray, list[list[tuple[int, int]]]]:
        n, m = obs.shape
        seg_id = -np.ones((n, m), dtype=np.int32)
        segments: list[list[tuple[int, int]]] = []
        sid = 0
        for c in range(m):
            r = 0
            while r < n:
                while r < n and obs[r, c]:
                    r += 1
                if r >= n:
                    break
                cells: list[tuple[int, int]] = []
                while r < n and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    r += 1
                segments.append(cells)
                sid += 1
        return seg_id, segments

    @staticmethod
    def _segments_diag(obs: np.ndarray) -> tuple[np.ndarray, list[list[tuple[int, int]]]]:
        # Main diagonals (r+1, c+1)
        n, m = obs.shape
        seg_id = -np.ones((n, m), dtype=np.int32)
        segments: list[list[tuple[int, int]]] = []
        sid = 0

        # Start points: top row (r=0, c=0..m-1)
        for start_c in range(m):
            r, c = 0, start_c
            while r < n and c < m:
                while r < n and c < m and obs[r, c]:
                    r += 1
                    c += 1
                if r >= n or c >= m:
                    break
                cells: list[tuple[int, int]] = []
                while r < n and c < m and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    r += 1
                    c += 1
                segments.append(cells)
                sid += 1

        # Start points: left column (r=1..n-1, c=0)
        for start_r in range(1, n):
            r, c = start_r, 0
            while r < n and c < m:
                while r < n and c < m and obs[r, c]:
                    r += 1
                    c += 1
                if r >= n or c >= m:
                    break
                cells: list[tuple[int, int]] = []
                while r < n and c < m and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    r += 1
                    c += 1
                segments.append(cells)
                sid += 1

        return seg_id, segments

    @staticmethod
    def _segments_adiag(obs: np.ndarray) -> tuple[np.ndarray, list[list[tuple[int, int]]]]:
        # Anti-diagonals (r+1, c-1)
        n, m = obs.shape
        seg_id = -np.ones((n, m), dtype=np.int32)
        segments: list[list[tuple[int, int]]] = []
        sid = 0

        # Start points: top row (r=0, c=0..m-1)
        for start_c in range(m):
            r, c = 0, start_c
            while r < n and c >= 0:
                while r < n and c >= 0 and obs[r, c]:
                    r += 1
                    c -= 1
                if r >= n or c < 0:
                    break
                cells: list[tuple[int, int]] = []
                while r < n and c >= 0 and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    r += 1
                    c -= 1
                segments.append(cells)
                sid += 1

        # Start points: right column (r=1..n-1, c=m-1)
        for start_r in range(1, n):
            r, c = start_r, m - 1
            while r < n and c >= 0:
                while r < n and c >= 0 and obs[r, c]:
                    r += 1
                    c -= 1
                if r >= n or c < 0:
                    break
                cells: list[tuple[int, int]] = []
                while r < n and c >= 0 and not obs[r, c]:
                    seg_id[r, c] = sid
                    cells.append((r, c))
                    r += 1
                    c -= 1
                segments.append(cells)
                sid += 1

        return seg_id, segments

    @staticmethod
    def _greedy_initial(
        free_mask: np.ndarray,
        row_id: np.ndarray,
        col_id: np.ndarray,
        diag_id: np.ndarray,
        adiag_id: np.ndarray,
        row_segments: list[list[tuple[int, int]]],
        col_segments: list[list[tuple[int, int]]],
        diag_segments: list[list[tuple[int, int]]],
        adiag_segments: list[list[tuple[int, int]]],
    ) -> list[tuple[int, int]]:
        import heapq

        n, m = free_mask.shape
        rs = np.array([len(s) for s in row_segments], dtype=np.int32) if row_segments else np.zeros(0, dtype=np.int32)
        cs = np.array([len(s) for s in col_segments], dtype=np.int32) if col_segments else np.zeros(0, dtype=np.int32)
        ds = np.array([len(s) for s in diag_segments], dtype=np.int32) if diag_segments else np.zeros(0, dtype=np.int32)
        as_ = np.array([len(s) for s in adiag_segments], dtype=np.int32) if adiag_segments else np.zeros(0, dtype=np.int32)

        r_used = np.zeros(rs.shape, dtype=bool)
        c_used = np.zeros(cs.shape, dtype=bool)
        d_used = np.zeros(ds.shape, dtype=bool)
        a_used = np.zeros(as_.shape, dtype=bool)

        heap: list[tuple[int, int, int, int]] = []
        idx_counter = 0
        for r in range(n):
            for c in range(m):
                if not free_mask[r, c]:
                    continue
                ri = int(row_id[r, c])
                ci = int(col_id[r, c])
                di = int(diag_id[r, c])
                ai = int(adiag_id[r, c])
                s = 0
                if ri >= 0:
                    s += int(rs[ri])
                if ci >= 0:
                    s += int(cs[ci])
                if di >= 0:
                    s += int(ds[di])
                if ai >= 0:
                    s += int(as_[ai])
                s -= 4
                heap.append((s, idx_counter, r, c))
                idx_counter += 1

        heapq.heapify(heap)
        sol: list[tuple[int, int]] = []

        while heap:
            _, _, r, c = heapq.heappop(heap)
            if not free_mask[r, c]:
                continue
            ri = int(row_id[r, c])
            ci = int(col_id[r, c])
            di = int(diag_id[r, c])
            ai = int(adiag_id[r, c])
            if (ri >= 0 and r_used[ri]) or (ci >= 0 and c_used[ci]) or (di >= 0 and d_used[di]) or (ai >= 0 and a_used[ai]):
                continue
            sol.append((r, c))
            if ri >= 0:
                r_used[ri] = True
                for rr, cc in row_segments[ri]:
                    free_mask[rr, cc] = False
            if ci >= 0:
                c_used[ci] = True
                for rr, cc in col_segments[ci]:
                    free_mask[rr, cc] = False
            if di >= 0:
                d_used[di] = True
                for rr, cc in diag_segments[di]:
                    free_mask[rr, cc] = False
            if ai >= 0:
                a_used[ai] = True
                for rr, cc in adiag_segments[ai]:
                    free_mask[rr, cc] = False

        return sol

    def solve(self, problem, **kwargs) -> Any:
        inst = np.asarray(problem, dtype=bool)
        n, m = inst.shape

        # No free cells
        if not (~inst).any():
            return []

        # Build segment structures
        row_id, row_segments = self._segments_rows(inst)
        col_id, col_segments = self._segments_cols(inst)
        diag_id, diag_segments = self._segments_diag(inst)
        adiag_id, adiag_segments = self._segments_adiag(inst)

        # Compute a single greedy solution globally to use as hints
        greedy_all = self._greedy_initial(
            (~inst).copy(),
            row_id,
            col_id,
            diag_id,
            adiag_id,
            row_segments,
            col_segments,
            diag_segments,
            adiag_segments,
        )
        greedy_all_set = set(greedy_all)

        # Map free cells to ids
        id_map = -np.ones((n, m), dtype=np.int32)
        cells_list: list[tuple[int, int]] = []
        k = 0
        for r in range(n):
            for c in range(m):
                if not inst[r, c]:
                    id_map[r, c] = k
                    cells_list.append((r, c))
                    k += 1
        if k == 0:
            return []

        # Union-Find to build independent components (union by segments)
        p = list(range(k))
        rk = [0] * k

        def find(x: int) -> int:
            while p[x] != x:
                p[x] = p[p[x]]
                x = p[x]
            return x

        def union(a: int, b: int) -> None:
            pa = find(a)
            pb = find(b)
            if pa == pb:
                return
            ra = rk[pa]
            rb = rk[pb]
            if ra < rb:
                p[pa] = pb
            elif ra > rb:
                p[pb] = pa
            else:
                p[pb] = pa
                rk[pa] += 1

        def union_segment(seg: list[tuple[int, int]]) -> None:
            if len(seg) <= 1:
                return
            # connect consecutive cells in the same segment
            prev = int(id_map[seg[0][0], seg[0][1]])
            for r1, c1 in seg[1:]:
                cur = int(id_map[r1, c1])
                union(prev, cur)
                prev = cur

        for seg in row_segments:
            union_segment(seg)
        for seg in col_segments:
            union_segment(seg)
        for seg in diag_segments:
            union_segment(seg)
        for seg in adiag_segments:
            union_segment(seg)

        # Build components
        comp_dict: dict[int, list[tuple[int, int]]] = {}
        for idx, (r, c) in enumerate(cells_list):
            root = find(idx)
            comp_dict.setdefault(root, []).append((r, c))

        # Reuse a single solver instance
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = False
        # Use multiple workers if available
        try:
            solver.parameters.num_search_workers = max(1, kwargs.get("num_search_workers", 8))
        except Exception:
            pass

        solution: list[tuple[int, int]] = []
        # Helper: simple Kuhn matching (sufficient for our small components)
        def matching_size_from_pairs(left_sids: set[int], right_sids: set[int], pairs: list[tuple[int, int]]) -> int:
            if not left_sids or not right_sids:
                return 0
            l_index = {sid: i for i, sid in enumerate(left_sids)}
            r_index = {sid: i for i, sid in enumerate(right_sids)}
            ln = len(l_index)
            rn = len(r_index)
            adj: list[list[int]] = [[] for _ in range(ln)]
            # Build adjacency
            for ls, rs in pairs:
                li = l_index.get(ls)
                ri = r_index.get(rs)
                if li is not None and ri is not None:
                    adj[li].append(ri)
            # Deduplicate neighbors
            for i in range(ln):
                if len(adj[i]) > 1:
                    adj[i] = list(set(adj[i]))
            match_r = [-1] * rn

            # Order left nodes by degree descending to speed up
            order = list(range(ln))
            order.sort(key=lambda u: len(adj[u]), reverse=True)

            def dfs(u: int, seen: list[bool]) -> bool:
                for v in adj[u]:
                    if seen[v]:
                        continue
                    seen[v] = True
                    if match_r[v] == -1 or dfs(match_r[v], seen):
                        match_r[v] = u
                        return True
                return False

            result = 0
            for u in order:
                seen = [False] * rn
                if dfs(u, seen):
                    result += 1
                    if result == min(ln, rn):
                        break
            return result

        # For each component, build and solve local model
        for comp_cells in comp_dict.values():
            comp_size = len(comp_cells)
            if comp_size == 0:
                continue
            if comp_size == 1:
                # Single cell, can always place a queen
                solution.append(comp_cells[0])
                continue

            # Determine segments present in this component
            row_sids: set[int] = set()
            col_sids: set[int] = set()
            dia_sids: set[int] = set()
            adi_sids: set[int] = set()
            for r, c in comp_cells:
                ri = int(row_id[r, c])
                ci = int(col_id[r, c])
                di = int(diag_id[r, c])
                ai = int(adiag_id[r, c])
                if ri >= 0:
                    row_sids.add(ri)
                if ci >= 0:
                    col_sids.add(ci)
                if di >= 0:
                    dia_sids.add(di)
                if ai >= 0:
                    adi_sids.add(ai)

            # Lower bound from global greedy, restricted to this component
            greedy_comp = [pos for pos in comp_cells if pos in greedy_all_set]
            lb = len(greedy_comp)

            # Compute simple tight upper bounds via bipartite matchings
            # Rows vs Cols
            pairs_rc = [(int(row_id[r, c]), int(col_id[r, c])) for r, c in comp_cells]
            ub_rc = matching_size_from_pairs(row_sids, col_sids, pairs_rc)
            # Diag vs Anti
            pairs_da = [(int(diag_id[r, c]), int(adiag_id[r, c])) for r, c in comp_cells]
            ub_da = matching_size_from_pairs(dia_sids, adi_sids, pairs_da)

            ub = min(
                ub_rc,
                ub_da,
                len(row_sids),
                len(col_sids),
                len(dia_sids),
                len(adi_sids),
                comp_size,
            )

            if lb >= ub:
                # Greedy is optimal for this component
                solution.extend(greedy_comp)
                continue

            # Build model for the component
            model = cp_model.CpModel()

            # Variables for component cells
            var_map: dict[tuple[int, int], cp_model.IntVar] = {}
            comp_vars: list[cp_model.IntVar] = []
            for r, c in comp_cells:
                v = model.NewBoolVar(f"x_{r}_{c}")
                var_map[(r, c)] = v
                comp_vars.append(v)

            def add_atmost_one_by_sid(sids: set[int], segments: list[list[tuple[int, int]]]) -> None:
                for sid in sids:
                    cells = segments[sid]
                    if len(cells) <= 1:
                        continue
                    vars_list = [var_map[(r, c)] for r, c in cells if (r, c) in var_map]
                    if len(vars_list) > 1:
                        model.AddAtMostOne(vars_list)

            add_atmost_one_by_sid(row_sids, row_segments)
            add_atmost_one_by_sid(col_sids, col_segments)
            add_atmost_one_by_sid(dia_sids, diag_segments)
            add_atmost_one_by_sid(adi_sids, adiag_segments)

            # Objective
            model.Maximize(sum(comp_vars))

            # Use greedy_comp hints and decision strategy
            if greedy_comp:
                model.Add(sum(comp_vars) >= len(greedy_comp))
                in_greedy = set(greedy_comp)
                ordered_vars: list[cp_model.IntVar] = []
                ordered_vars.extend(var_map[pos] for pos in greedy_comp if pos in var_map)
                if len(ordered_vars) < len(comp_vars):
                    rest = [v for pos, v in var_map.items() if pos not in in_greedy]
                    ordered_vars.extend(rest)
                model.AddDecisionStrategy(
                    ordered_vars,
                    cp_model.CHOOSE_FIRST,
                    cp_model.SELECT_MAX_VALUE,
                )
                for pos, v in var_map.items():
                    model.AddHint(v, 1 if pos in in_greedy else 0)

            # Solve component
            status = solver.Solve(model)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                for pos, v in var_map.items():
                    if solver.Value(v) == 1:
                        solution.append(pos)
            else:
                # Fallback to greedy if solver fails (should rarely happen)
                solution.extend(greedy_comp)

        return solution
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
