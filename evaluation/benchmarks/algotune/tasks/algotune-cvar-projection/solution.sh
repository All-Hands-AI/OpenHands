#!/bin/bash

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
