#!/bin/bash

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
