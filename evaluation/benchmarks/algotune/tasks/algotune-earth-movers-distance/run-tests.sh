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
PROBLEM_SIZE = 1151           # Task difficulty (i.e. "n" in AlgoTune)
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

from typing import Any, Dict

import numpy as np
import ot

def _emd_2x2(a: np.ndarray, b: np.ndarray, M: np.ndarray | list) -> np.ndarray | None:
    """
    Closed-form optimal transport for 2x2 case when the solution is unique (c != 0).
    Returns None if tie (c == 0), so caller can fall back to ot.lp.emd to match reference tie-breaking.
    """
    # a = [a1, a2], b = [b1, b2]
    a1, a2 = float(a[0]), float(a[1])
    b1, b2 = float(b[0]), float(b[1])

    # Feasible interval for g11
    lo = max(0.0, a1 - b2)
    hi = min(a1, b1)

    # Extract costs
    if isinstance(M, np.ndarray):
        M00 = float(M[0, 0])
        M01 = float(M[0, 1])
        M10 = float(M[1, 0])
        M11 = float(M[1, 1])
    else:
        M00 = float(M[0][0])
        M01 = float(M[0][1])
        M10 = float(M[1][0])
        M11 = float(M[1][1])

    # Determine which bound minimizes cost
    c = M00 - M01 - M10 + M11
    if c == 0.0:
        return None  # tie; let POT decide to match exactly

    g11 = hi if c < 0.0 else lo
    g12 = a1 - g11
    g21 = b1 - g11
    g22 = a2 - g21

    # Clean extremely small negatives due to floating arithmetic
    tol = 1e-15

    def _clip(x: float) -> float:
        return 0.0 if abs(x) < tol else x

    G = np.array([[ _clip(g11), _clip(g12)],
                  [ _clip(g21), _clip(g22)]], dtype=np.float64)
    return G

def _north_west_corner(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # Construct a feasible (and optimal for Monge) transport plan via the north-west corner rule.
    a_rem = a.astype(np.float64, copy=True)
    b_rem = b.astype(np.float64, copy=True)
    n, m = a_rem.size, b_rem.size
    G = np.zeros((n, m), dtype=np.float64)

    i = 0
    j = 0
    tol = 1e-15
    while i < n and j < m:
        mass = a_rem[i] if a_rem[i] <= b_rem[j] else b_rem[j]
        G[i, j] = mass
        a_rem[i] -= mass
        b_rem[j] -= mass

        ai_zero = a_rem[i] <= tol
        bj_zero = b_rem[j] <= tol
        if ai_zero and bj_zero:
            i += 1
            j += 1
        elif ai_zero:
            i += 1
        elif bj_zero:
            j += 1
        else:
            # Should not happen if sums match and all nonnegative; robustly advance
            j += 1

    return G

def _is_strict_monge_full(M: np.ndarray) -> bool:
    # Full vectorized strict Monge check on all adjacent 2x2 minors.
    if M.shape[0] < 2 or M.shape[1] < 2:
        return True  # Trivially Monge
    A = M[:-1, :-1]
    B = M[1:, 1:]
    C = M[:-1, 1:]
    D = M[1:, :-1]
    scale = float(np.max(np.abs(M)))
    tol = 1e-12 * (scale + 1.0)
    return np.all(A + B <= C + D - tol)

def _is_strict_monge(M: np.ndarray) -> bool:
    # Fast early-exit sampling followed by full check only if sampling passes.
    n, m = M.shape
    if n < 2 or m < 2:
        return True
    nr = n - 1
    mr = m - 1
    total = nr * mr
    # Small cases: do full check
    if total <= 256:
        return _is_strict_monge_full(M)

    # Sampling grid
    scale = float(np.max(np.abs(M)))
    tol = 1e-12 * (scale + 1.0)
    # Choose about 64 samples spread roughly evenly
    target = 64
    si = max(1, nr // int(np.sqrt(target)))
    sj = max(1, mr // int(np.sqrt(target)))
    i = 0
    while i < nr:
        j = 0
        while j < mr:
            if not (M[i, j] + M[i + 1, j + 1] <= M[i, j + 1] + M[i + 1, j] - tol):
                return False
            j += sj
        i += si

    # Passed sampling, confirm with full check to ensure strictness
    return _is_strict_monge_full(M)

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Any:
        """
        Fast EMD solver that matches POT's ot.lp.emd exactly by:
          - Handling trivial/degenerate cases directly
          - Removing zero-mass rows/columns before calling ot.lp.emd (and expanding back)
          - Using a closed-form 2x2 unique-solution shortcut
          - Using NW corner rule for strictly Monge costs (unique optimal plan)
          - Falling back to ot.lp.emd for general cases

        Returns {"transport_plan": np.ndarray of shape (n, m)}.
        """
        a_in = problem["source_weights"]
        b_in = problem["target_weights"]
        M_in = problem["cost_matrix"]

        # Zero-copy when possible for a and b
        a = a_in if isinstance(a_in, np.ndarray) and a_in.dtype == np.float64 else np.asarray(a_in, dtype=np.float64)
        b = b_in if isinstance(b_in, np.ndarray) and b_in.dtype == np.float64 else np.asarray(b_in, dtype=np.float64)

        n, m = a.shape[0], b.shape[0]

        # Trivial shapes
        if n == 1:
            return {"transport_plan": b.reshape(1, -1)}
        if m == 1:
            return {"transport_plan": a.reshape(-1, 1)}

        # Precompute nonzero indices once to avoid multiple scans
        I = np.flatnonzero(a)
        J = np.flatnonzero(b)

        # If exactly one nonzero in a: unique plan
        if I.size == 1:
            i = int(I[0])
            G = np.zeros((n, m), dtype=np.float64)
            G[i, :] = b
            return {"transport_plan": G}

        # Remove zero-mass rows/columns to speed up LP without changing the solution
        if I.size != n or J.size != m:
            # Reduced problem
            a_r = a[I]
            b_r = b[J]
            # Build reduced cost matrix lazily
            if isinstance(M_in, np.ndarray):
                M_r = M_in[np.ix_(I, J)]
            else:
                M_r = np.asarray(M_in, dtype=np.float64)[np.ix_(I, J)]
            nr, mr = a_r.size, b_r.size

            # Trivial reduced shapes
            if nr == 1:
                G_full = np.zeros((n, m), dtype=np.float64)
                G_full[I[0], J] = b_r
                return {"transport_plan": G_full}
            if mr == 1:
                G_full = np.zeros((n, m), dtype=np.float64)
                G_full[I, J[0]] = a_r
                return {"transport_plan": G_full}

            # 2x2 unique solution closed-form
            if nr == 2 and mr == 2:
                G_r = _emd_2x2(a_r, b_r, M_r)
                if G_r is not None:
                    G_full = np.zeros((n, m), dtype=np.float64)
                    G_full[np.ix_(I, J)] = G_r
                    return {"transport_plan": G_full}

            # General reduced case via POT
            if isinstance(M_r, np.ndarray) and M_r.dtype == np.float64 and M_r.flags.c_contiguous:
                M_cont = M_r
            else:
                M_cont = np.ascontiguousarray(M_r, dtype=np.float64)
            G_r = ot.lp.emd(a_r, b_r, M_cont, check_marginals=False)

            G_full = np.zeros((n, m), dtype=np.float64)
            G_full[np.ix_(I, J)] = G_r
            return {"transport_plan": G_full}

        # No zeros to remove. Try 2x2 unique closed-form
        if n == 2 and m == 2:
            # Pass M_in directly to avoid unnecessary conversion
            G = _emd_2x2(a, b, M_in)
            if G is not None:
                return {"transport_plan": G}

        # Strict Monge: NW rule optimal and unique (only check small problems)
        if n * m <= 256:
            if isinstance(M_in, np.ndarray):
                M_small = M_in
            else:
                M_small = np.asarray(M_in, dtype=np.float64)
            if _is_strict_monge(M_small):
                G = _north_west_corner(a, b)
                return {"transport_plan": G}

        # General case via POT
        # Ensure M is C-contiguous float64 as required by ot.lp.emd
        if isinstance(M_in, np.ndarray) and M_in.dtype == np.float64 and M_in.flags.c_contiguous:
            M = M_in
        else:
            M = np.ascontiguousarray(M_in, dtype=np.float64)

        G = ot.lp.emd(a, b, M, check_marginals=False)
        return {"transport_plan": G}
        return {"transport_plan": G}
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
