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
PROBLEM_SIZE = 278           # Task difficulty (i.e. "n" in AlgoTune)
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

from typing import Any, Dict, Tuple

import numpy as np

try:
    import cvxpy as cp  # type: ignore
except Exception:  # pragma: no cover
    cp = None  # Fallback handled below

# Optional direct OSQP path (faster than going through CVXPY)
try:
    import osqp  # type: ignore
    from scipy import sparse as sp  # type: ignore
except Exception:  # pragma: no cover
    osqp = None
    sp = None

# Optional fast dense linear algebra (Cholesky) from SciPy
try:
    from scipy import linalg as spla  # type: ignore
except Exception:  # pragma: no cover
    spla = None

class Solver:
    def _read_problem(self, problem: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        # Accept either "P" or "Q" for the Hessian
        P_like = problem.get("P", problem.get("Q"))
        if P_like is None:
            raise ValueError("Problem must contain key 'P' (or 'Q').")
        P = np.asarray(P_like, dtype=float)
        if P.ndim != 2 or P.shape[0] != P.shape[1]:
            raise ValueError("P must be a square 2D array.")

        q = np.asarray(problem.get("q", []), dtype=float).reshape(-1)
        if q.size == 0:
            q = np.zeros(P.shape[0], dtype=float)
        if q.ndim != 1 or q.shape[0] != P.shape[0]:
            raise ValueError("q must be a 1D array of length n (matching P).")

        n = P.shape[0]

        # Handle possibly missing or empty G/h and A/b
        G_like = problem.get("G", [])
        h_like = problem.get("h", [])
        G = np.asarray(G_like, dtype=float)
        h = np.asarray(h_like, dtype=float).reshape(-1)

        if G.size == 0:
            G = np.zeros((0, n), dtype=float)
            h = np.zeros((0,), dtype=float)
        else:
            if G.ndim == 1:
                if G.shape[0] == n:
                    G = G.reshape(1, n)
                else:
                    raise ValueError("G must be (m, n).")
            if G.shape[1] != n:
                raise ValueError("G must be (m, n).")
            if h.size == 0:
                h = np.zeros(G.shape[0], dtype=float)
            if h.shape[0] != G.shape[0]:
                raise ValueError("h must be length m to match G @ x <= h.")

        A_like = problem.get("A", [])
        b_like = problem.get("b", [])
        A = np.asarray(A_like, dtype=float)
        b = np.asarray(b_like, dtype=float).reshape(-1)

        if A.size == 0:
            A = np.zeros((0, n), dtype=float)
            b = np.zeros((0,), dtype=float)
        else:
            if A.ndim == 1:
                if A.shape[0] == n:
                    A = A.reshape(1, n)
                else:
                    raise ValueError("A must be (p, n).")
            if A.shape[1] != n:
                raise ValueError("A must be (p, n).")
            if b.size == 0:
                b = np.zeros(A.shape[0], dtype=float)
            if b.shape[0] != A.shape[0]:
                raise ValueError("b must be length p to match A @ x == b.")

        return P, q, G, h, A, b

    @staticmethod
    def _symmetrize(P: np.ndarray) -> np.ndarray:
        return 0.5 * (P + P.T)

    @staticmethod
    def _objective(P: np.ndarray, q: np.ndarray, x: np.ndarray) -> float:
        return 0.5 * float(x @ P @ x) + float(q @ x)

    @staticmethod
    def _solve_unconstrained(P: np.ndarray, q: np.ndarray) -> np.ndarray:
        # Solve P x + q = 0
        # Try fast Cholesky if PD
        if spla is not None:
            try:
                c, lower = spla.cho_factor(P, lower=True, check_finite=False)
                x = -spla.cho_solve((c, lower), q, check_finite=False)
                return x
            except Exception:
                pass
        try:
            x = -np.linalg.solve(P, q)
            return x
        except np.linalg.LinAlgError:
            # Use least-squares (minimum-norm solution) if singular
            x = -np.linalg.lstsq(P, q, rcond=None)[0]
            return x

    @staticmethod
    def _solve_equality_qp(P: np.ndarray, q: np.ndarray, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        n = P.shape[0]
        p = A.shape[0]
        if p == 0:
            return Solver._solve_unconstrained(P, q)

        # Schur complement approach: solve P X = [A^T, q]
        try:
            if spla is not None:
                try:
                    c, lower = spla.cho_factor(P, lower=True, check_finite=False)
                    B = np.column_stack((A.T, q))
                    Y = spla.cho_solve((c, lower), B, check_finite=False)
                except Exception:
                    B = np.column_stack((A.T, q))
                    Y = np.linalg.solve(P, B)
            else:
                B = np.column_stack((A.T, q))
                Y = np.linalg.solve(P, B)
            Pinv_AT = Y[:, :p]  # (n, p)
            Pinv_q = Y[:, p]    # (n,)
            S = A @ Pinv_AT     # (p, p)
            rhs = -(b + A @ Pinv_q)
            try:
                nu = np.linalg.solve(S, rhs)
            except np.linalg.LinAlgError:
                nu = np.linalg.lstsq(S, rhs, rcond=None)[0]
            x = -Pinv_q - Pinv_AT @ nu
            if np.allclose(A @ x, b, atol=1e-9, rtol=0):
                return x
        except np.linalg.LinAlgError:
            pass

        # Fallback: solve KKT system [P A^T; A 0] [x; nu] = [-q; b]
        K = np.block([[P, A.T], [A, np.zeros((p, p), dtype=P.dtype)]])
        rhs_full = np.concatenate((-q, b))
        try:
            z = np.linalg.solve(K, rhs_full)
            x = z[:n]
            if np.allclose(A @ x, b, atol=1e-8, rtol=0):
                return x
        except np.linalg.LinAlgError:
            z = np.linalg.lstsq(K, rhs_full, rcond=None)[0]
            x = z[:n]
            if np.allclose(A @ x, b, atol=1e-8, rtol=0):
                return x

        # If numerical issues, return anyway (let caller validate) or fallback to cvxpy path.
        return x

    def _solve_with_osqp(
        self, P: np.ndarray, q: np.ndarray, G: np.ndarray, h: np.ndarray, A: np.ndarray, b: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        if osqp is None or sp is None:
            raise RuntimeError("OSQP not available")

        n = P.shape[0]

        m = G.shape[0]
        p = A.shape[0]
        if m == 0 and p == 0:
            x = self._solve_unconstrained(P, q)
            return x, self._objective(P, q, x)

        # Build sparse P (upper triangular) and constraint matrix once
        P_csc = sp.csc_matrix(np.triu(P))
        if m > 0 and p > 0:
            A_sp = sp.vstack([sp.csc_matrix(G), sp.csc_matrix(A)], format="csc")
            l = np.concatenate([np.full(m, -np.inf), b])
            u = np.concatenate([h, b])
        elif m > 0:
            A_sp = sp.csc_matrix(G)
            l = np.full(m, -np.inf)
            u = h
        else:  # p > 0
            A_sp = sp.csc_matrix(A)
            l = b
            u = b

        # Replace infinities with OSQP's large bound
        OSQP_INF = 1e30
        l = np.array(l, dtype=float, copy=True)
        u = np.array(u, dtype=float, copy=True)
        l[np.isneginf(l)] = -OSQP_INF
        u[np.isposinf(u)] = OSQP_INF

        # Phase 1: faster solve
        prob = osqp.OSQP()
        prob.setup(
            P=P_csc,
            q=q,
            A=A_sp,
            l=l,
            u=u,
            eps_abs=1e-6,
            eps_rel=1e-6,
            max_iter=2000,
            polish=False,
            verbose=False,
        )
        res = prob.solve()
        status = str(getattr(res.info, "status", "")).lower()
        if ("solved" in status) and (res.x is not None):
            x = np.asarray(res.x, dtype=float).reshape(n)
            # Quick feasibility check; tighten if needed
            need_refine = False
            if m > 0:
                viol = float(np.max(np.maximum(G @ x - h, 0.0))) if m > 0 else 0.0
                if not np.isfinite(viol) or viol > 1e-6:
                    need_refine = True
            if not need_refine and p > 0:
                eq_res = float(np.max(np.abs(A @ x - b))) if p > 0 else 0.0
                if not np.isfinite(eq_res) or eq_res > 1e-6:
                    need_refine = True
            if not need_refine:
                obj = float(getattr(res.info, "obj_val", self._objective(P, q, x)))
                return x, obj

        # Phase 2: stricter settings with polish; reuse factorization/warm start
        try:
            prob.update(eps_abs=1e-8, eps_rel=1e-8, max_iter=10000, polish=True)
        except Exception:
            # some versions require passing only supported kwargs
            prob.update(eps_abs=1e-8, eps_rel=1e-8, max_iter=10000)
        res = prob.solve()
        status = str(getattr(res.info, "status", "")).lower()
        if ("solved" not in status) or (res.x is None):
            raise RuntimeError(f"OSQP failed with status: {getattr(res.info, 'status', '')}")

        x = np.asarray(res.x, dtype=float).reshape(n)
        # Final feasibility check to ensure validator acceptance
        if m > 0:
            viol = float(np.max(np.maximum(G @ x - h, 0.0)))
            if not np.isfinite(viol) or viol > 1e-6:
                raise RuntimeError("OSQP solution violates inequality constraints beyond tolerance.")
        if p > 0:
            eq_res = float(np.max(np.abs(A @ x - b)))
            if not np.isfinite(eq_res) or eq_res > 1e-6:
                raise RuntimeError("OSQP solution violates equality constraints beyond tolerance.")

        obj = float(getattr(res.info, "obj_val", self._objective(P, q, x)))
        return x, obj

    def _solve_with_cvxpy(self, P: np.ndarray, q: np.ndarray, G: np.ndarray, h: np.ndarray, A: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, float]:
        if cp is None:
            raise RuntimeError("cvxpy is required for inequality-constrained problems.")

        n = P.shape[0]
        x = cp.Variable(n)
        objective = 0.5 * cp.quad_form(x, cp.psd_wrap(P)) + q @ x
        constraints = []
        if G.shape[0] > 0:
            constraints.append(G @ x <= h)
        if A.shape[0] > 0:
            constraints.append(A @ x == b)
        prob = cp.Problem(cp.Minimize(objective), constraints)

        # Use OSQP via CVXPY with strict tolerances to ensure feasibility
        try:
            val = prob.solve(
                solver=cp.OSQP,
                eps_abs=1e-8,
                eps_rel=1e-8,
                polish=True,
                warm_start=True,
                verbose=False,
            )
        except Exception:
            val = None

        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            # Final fallback: ECOS (QP as SOCP)
            try:
                val = prob.solve(solver=cp.ECOS, abstol=1e-8, reltol=1e-8, feastol=1e-8, verbose=False)
            except Exception:
                pass

        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise ValueError(f"Solver failed (status = {prob.status})")

        x_val = np.asarray(x.value, dtype=float).reshape(-1)
        if val is None or not np.isfinite(val):
            val = self._objective(P, q, x_val)
        return x_val, float(val)

    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        P, q, G, h, A, b = self._read_problem(problem)

        # Symmetrize P for numerical stability
        P = self._symmetrize(P)

        m = G.shape[0]
        p = A.shape[0]

        # Fast paths
        if m == 0 and p == 0:
            x = self._solve_unconstrained(P, q)
            return {"solution": x.tolist(), "objective": self._objective(P, q, x)}
        if m == 0 and p > 0:
            x = self._solve_equality_qp(P, q, A, b)
            # Ensure feasibility within tolerance; otherwise fall back to inequality-capable solver
            if np.allclose(A @ x, b, atol=1e-7, rtol=0):
                return {"solution": x.tolist(), "objective": self._objective(P, q, x)}

        # General case (inequalities and/or equalities): try OSQP directly, then CVXPY
        if osqp is not None and sp is not None:
            try:
                x, obj = self._solve_with_osqp(P, q, G, h, A, b)
                return {"solution": x.tolist(), "objective": float(obj)}
            except Exception:
                pass

        # Fallback to CVXPY
        x, obj = self._solve_with_cvxpy(P, q, G, h, A, b)
        return {"solution": x.tolist(), "objective": float(obj)}
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
