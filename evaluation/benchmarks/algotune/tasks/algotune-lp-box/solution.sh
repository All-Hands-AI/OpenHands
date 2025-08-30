#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from scipy.optimize import linprog

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, List[float]]:
        """
        Solve the LP Box problem:
            minimize    c^T x
            subject to  A x <= b
                        0 <= x <= 1

        Parameters
        ----------
        problem : dict
            Dictionary with keys:
              - "c": list of length n (objective coefficients)
              - "A": list of m lists (inequality matrix)
              - "b": list of length m (inequality rhs)

        Returns
        -------
        dict
            {"solution": list of length n} the optimal primal solution.
        """
        c = np.asarray(problem["c"], dtype=float).ravel()
        n = c.size

        # Handle A, b possibly missing or empty
        A_list = problem.get("A", [])
        b_list = problem.get("b", [])

        if A_list is None:
            A = np.empty((0, n), dtype=float)
            b = np.empty((0,), dtype=float)
        else:
            A = np.asarray(A_list, dtype=float)
            if A.ndim == 1 and A.size != 0:
                A = A.reshape(1, -1)
            if A.size == 0:
                A = np.empty((0, n), dtype=float)
            else:
                # Ensure correct shape if possible
                if A.shape[1] != n:
                    A = A.reshape(-1, n)
            b = (
                np.asarray(b_list, dtype=float).ravel()
                if b_list is not None
                else np.empty((0,), dtype=float)
            )

        m = A.shape[0]

        # Fast path: no inequality constraints -> box-only LP
        if m == 0:
            # Minimization over [0,1]^n: choose x_i = 1 if c_i < 0 else 0
            x = np.where(c < 0.0, 1.0, 0.0)
            return {"solution": x.tolist()}

        # Quick feasibility checks for trivial candidates
        x0 = np.where(c < 0.0, 1.0, 0.0)  # Box-optimum ignoring Ax<=b
        # Check x0 feasibility
        if A.shape[1] == n and b.size == m:
            Ax0 = A @ x0
            if np.all(Ax0 <= b + 1e-12):
                return {"solution": x0.tolist()}
        # Check all-zero feasibility (often feasible and optimal when c >= 0)
        x_zero = np.zeros(n, dtype=float)
        Ax_zero_ok = False
        if A.shape[1] == n and b.size == m:
            Ax_zero_ok = np.all((A @ x_zero) <= b + 1e-12)
            if Ax_zero_ok and np.all(c >= 0):
                return {"solution": x_zero.tolist()}
            # Check all-ones feasibility fast path when objective prefers ones
            if np.all(c <= 0.0):
                x_one = np.ones(n, dtype=float)
                if np.all((A @ x_one) <= b + 1e-12):
                    return {"solution": x_one.tolist()}

        # Remove constraints that are redundant given 0<=x<=1:
        # For row i, max over box is sum(max(A[i,j],0)). If this <= b_i, constraint is redundant.
        # Vectorized computation of positive row sums
        pos_row_sum = np.sum(np.maximum(A, 0.0), axis=1)
        # Keep only potentially active constraints
        keep = pos_row_sum > (b + 1e-12)
        if np.any(~keep):
            A = A[keep]
            b = b[keep]
            m = A.shape[0]
            if m == 0:
                # All constraints redundant; return box-only optimum
                x = np.where(c < 0.0, 1.0, 0.0)
                return {"solution": x.tolist()}
            # Re-check feasibility of x0 on the reduced system
            Ax0 = A @ x0
            if np.all(Ax0 <= b + 1e-12):
                return {"solution": x0.tolist()}
            if Ax_zero_ok:
                Ax_zero_red_ok = np.all((A @ x_zero) <= b + 1e-12)
                if Ax_zero_red_ok and np.all(c >= 0):
                    return {"solution": x_zero.tolist()}

        bounds = [(0.0, 1.0)] * n

        # Variable fixing using column monotonicity:
        # - If column j is <= 0 for all rows and c_j < 0, set x_j = 1 (improves objective and cannot hurt feasibility).
        # - If column j is >= 0 for all rows and c_j >= 0, set x_j = 0 (cannot hurt feasibility and is objective-preferable).
        if m > 0:
            col_all_nonpos = np.all(A <= 0.0, axis=0)
            col_all_nonneg = np.all(A >= 0.0, axis=0)
            fix_one_mask = col_all_nonpos & (c < 0.0)
            fix_zero_mask = col_all_nonneg & (c >= 0.0)

            if np.any(fix_one_mask) or np.any(fix_zero_mask):
                x_full = np.zeros(n, dtype=float)
                x_full[fix_one_mask] = 1.0  # fix to 1 where safe and beneficial
                # zeros already set for fix_zero_mask, and remain 0 for others until solved

                free_mask = ~(fix_one_mask | fix_zero_mask)
                if np.any(free_mask):
                    # Reduce problem
                    A_red = A[:, free_mask]
                    # Adjust rhs for fixed ones (making constraints looser)
                    if np.any(fix_one_mask):
                        b_red = b - A[:, fix_one_mask] @ np.ones(int(np.count_nonzero(fix_one_mask)))
                    else:
                        b_red = b.copy()
                    c_red = c[free_mask]
                    x0_free = (c_red < 0.0).astype(float)

                    # Second-stage redundancy elimination on reduced system
                    if A_red.shape[0] > 0:
                        pos_row_sum_red = np.sum(np.maximum(A_red, 0.0), axis=1)
                        keep_red = pos_row_sum_red > (b_red + 1e-12)
                        if np.any(~keep_red):
                            A_red = A_red[keep_red]
                            b_red = b_red[keep_red]

                    if A_red.shape[0] == 0:
                        # No active constraints remain
                        x_full[free_mask] = x0_free
                        return {"solution": np.clip(x_full, 0.0, 1.0).tolist()}

                    # Quick checks on reduced problem
                    if np.all(A_red @ x0_free <= b_red + 1e-12):
                        x_full[free_mask] = x0_free
                        return {"solution": np.clip(x_full, 0.0, 1.0).tolist()}

                    if np.all(c_red >= 0.0):
                        x_zero_free = np.zeros_like(c_red)
                        if np.all(A_red @ x_zero_free <= b_red + 1e-12):
                            x_full[free_mask] = x_zero_free
                            return {"solution": x_full.tolist()}

                    # Solve reduced LP
                    bounds_red = [(0.0, 1.0)] * int(np.count_nonzero(free_mask))
                    res = linprog(c_red, A_ub=A_red, b_ub=b_red, bounds=bounds_red, method="highs")

                    x_free_sol = res.x if (res.success and (res.x is not None)) else x0_free
                    x_full[free_mask] = x_free_sol
                    # Numerical safety: clip to box
                    x_full = np.clip(x_full, 0.0, 1.0)
                    return {"solution": x_full.tolist()}
                else:
                    # All variables fixed
                    return {"solution": x_full.tolist()}

        # Solve with HiGHS on the (possibly reduced) original system
        res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

        x_res = res.x if (res.success and (res.x is not None)) else x0

        # Numerical safety: clip to box
        x_res = np.clip(np.asarray(x_res, dtype=float), 0.0, 1.0)

        return {"solution": x_res.tolist()}
EOF
