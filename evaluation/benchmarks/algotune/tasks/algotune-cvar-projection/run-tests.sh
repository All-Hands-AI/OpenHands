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

class Solver:
    def __init__(self) -> None:
        # Optional defaults if problem dict omits keys (not expected per spec)
        self.default_beta = 0.95
        self.default_kappa = 1.0

    def solve(self, problem, **kwargs) -> Any:
        """
        Project x0 onto the set {x : sum_largest(Ax, k) <= alpha}, where
        k = int((1 - beta) * n_scenarios), alpha = kappa * k.

        Uses a cutting-plane method on the dual representation
        sum_largest(y, k) = max_{w in [0,1]^m, sum w = k} w^T y,
        iteratively adding the most violated halfspace and projecting onto the
        intersection of accumulated halfspaces via a specialized QP solver
        (dual coordinate descent).
        """
        try:
            x0 = np.asarray(problem["x0"], dtype=float)
            A = np.asarray(problem["loss_scenarios"], dtype=float)
            beta = float(problem.get("beta", self.default_beta))
            kappa = float(problem.get("kappa", self.default_kappa))
        except Exception:
            return {"x_proj": []}

        if x0.ndim != 1 or A.ndim != 2 or A.shape[1] != x0.shape[0]:
            return {"x_proj": []}

        m, n = A.shape
        # Match reference behavior for k calculation
        k = int((1.0 - beta) * m)
        if k <= 0:
            # Degenerate case; mirror reference's implicit expectation that k >= 1
            # Return x0 (no constraint effectively enforced), as CVaR undefined for k=0.
            return {"x_proj": x0.tolist()}
        if k > m:
            k = m  # Just in case of numerical issues

        alpha = kappa * k

        # Quick feasibility check for x0
        y0 = A @ x0
        # sum of k largest entries
        # handle k == m by simple sum
        if k == m:
            sum_topk = float(np.sum(y0))
        else:
            # np.partition: k largest are at positions [m-k:]
            idx = m - k
            # Guard idx may be 0 if k == m which is handled above
            part = np.partition(y0, idx)
            sum_topk = float(np.sum(part[idx:]))

        if sum_topk <= alpha + 1e-10:
            return {"x_proj": x0.tolist()}

        # Cutting-plane structures
        seen_sets: set = set()  # to avoid duplicate cuts (store frozenset of indices)
        # Dual QP data for projection onto {C x <= alpha}:
        # minimize 0.5||x - x0||^2 s.t. c_j^T x <= alpha
        # Dual: minimize 0.5 λ^T G λ - q^T λ, λ >= 0
        # where G = C C^T, q_i = c_i^T x0 - alpha
        G = np.zeros((0, 0), dtype=float)
        q = np.zeros((0,), dtype=float)
        lam = np.zeros((0,), dtype=float)
        g = np.zeros((0,), dtype=float)  # gradient g = G lam - q (also primal slacks)
        # Maintain constraint matrix C (rows are c_j)
        C_mat = np.empty((0, n), dtype=float)

        # Helper functions
        def topk_indices(vals: np.ndarray, kk: int) -> np.ndarray:
            if kk >= vals.shape[0]:
                return np.arange(vals.shape[0], dtype=int)
            idx_split = vals.shape[0] - kk
            part_idx = np.argpartition(vals, idx_split)[idx_split:]
            return part_idx

        def add_cut(c: np.ndarray) -> None:
            # Expand G, q, lam, g with new constraint row/col and update C_mat
            nonlocal G, q, lam, g, C_mat
            p_old = G.shape[0]
            c = c.astype(float, copy=False).reshape(1, -1)
            if p_old == 0:
                # Initialize structures
                C_mat = c.copy()
                cc = float(c @ c.T)
                G = np.array([[cc]], dtype=float)
                q = np.array([float(c @ x0 - alpha)], dtype=float)
                lam = np.zeros((1,), dtype=float)
                g = -q.copy()  # since g = G*lam - q and lam=0
            else:
                # Vectorized inner products with existing constraints
                new_col = (C_mat @ c.T).ravel()  # shape (p_old,)
                new_diag = float(c @ c.T)
                # build new G
                G_expanded = np.empty((p_old + 1, p_old + 1), dtype=float)
                G_expanded[:p_old, :p_old] = G
                G_expanded[:p_old, p_old] = new_col
                G_expanded[p_old, :p_old] = new_col
                G_expanded[p_old, p_old] = new_diag
                G = G_expanded
                # expand q, lam, g
                C_mat = np.vstack((C_mat, c))
                q = np.concatenate([q, np.array([float(c @ x0 - alpha)], dtype=float)])
                lam = np.concatenate([lam, np.array([0.0], dtype=float)])
                # g_old remains same for old entries; new g_p = sum_j G_pj lam_j - q_p
                g_new = float(new_col @ lam[:p_old] - q[p_old])
                g = np.concatenate([g, np.array([g_new], dtype=float)])

        def dual_cd_solve(max_iters: int = 10000, tol: float = 1e-10) -> None:
            # Cyclic coordinate descent on dual: λ_i ← max(0, λ_i - g_i / G_ii)
            nonlocal G, q, lam, g
            p = lam.shape[0]
            if p == 0:
                return
            # Early exit if already good
            if np.min(g) >= -tol:
                return
            # Precompute diagonal
            diag = np.diag(G).copy()
            # To avoid division by zero, regularize tiny diagonals
            diag[diag <= 0.0] = 1e-16

            # Perform sweeps
            for _ in range(max_iters):
                improved = False
                for i in range(p):
                    gi = g[i]
                    # projected coordinate update
                    li = lam[i]
                    new_li = li - gi / diag[i]
                    if new_li < 0.0:
                        new_li = 0.0
                    delta = new_li - li
                    if delta != 0.0:
                        lam[i] = new_li
                        # Update gradient g = G lam - q
                        # Only need to add delta * G[:, i]
                        g += delta * G[:, i]
                        improved = True
                # Check feasibility (primal slacks >= -tol) and complementarity approx
                if np.min(g) >= -tol:
                    break
                if not improved:
                    # No change in λ in a full sweep -> stagnation
                    break

        # Outer cutting-plane loop
        max_outer = 200
        # tolerance for CVaR feasibility and halfspace projection
        cvar_tol = 1e-8

        x_curr = x0.copy()
        for _ in range(max_outer):
            y = A @ x_curr
            idx_k = topk_indices(y, k)
            sum_k = float(np.sum(y[idx_k]))
            if sum_k <= alpha + cvar_tol:
                # Feasible for true CVaR constraint
                return {"x_proj": x_curr.tolist()}

            # Add most violated cut: c = sum_{i in top-k} A_i
            # Avoid duplicate cuts
            key = tuple(sorted(map(int, idx_k.tolist())))
            if key not in seen_sets:
                seen_sets.add(key)
                c = np.sum(A[idx_k, :], axis=0)
                add_cut(c)

            # Project x0 onto current intersection {c_j^T x <= alpha}
            dual_cd_solve(max_iters=20000, tol=1e-10)
            if lam.size > 0:
                # x = x0 - C^T lam
                x_curr = x0 - C_mat.T @ lam
            else:
                x_curr = x0.copy()

        # If not converged within max_outer, return best found if feasible or last projection
        # Ensure at least returns something
        return {"x_proj": x_curr.tolist()}
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
