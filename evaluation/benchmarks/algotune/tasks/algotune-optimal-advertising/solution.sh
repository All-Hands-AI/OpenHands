#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict
import json

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Solve the optimal advertising problem via a fast LP reformulation.

        Reformulation:
            Introduce variables t_i representing realized revenue for ad i.
            Maximize sum_i t_i subject to:
              - t_i <= B_i
              - t_i <= R_i * sum_t P_it * D_it
              - D_it >= 0
              - sum_i D_it <= T_t  (capacity per time slot)
              - sum_t D_it >= c_i  (min display requirement per ad)

        We encode the LP for SciPy's HiGHS:
            Variables: x = [vec(D) ; t], size m*n + m
            Objective: maximize sum(t) -> minimize -sum(t)

        :param problem: Dictionary with problem parameters
        :return: Solution dictionary
        """
        # Allow JSON string input for eval_input convenience
        if isinstance(problem, str):
            try:
                problem = json.loads(problem)
            except Exception:
                return {"status": "invalid_input_format", "optimal": False}

        # Extract and validate inputs
        P = np.asarray(problem["P"], dtype=float)
        R = np.asarray(problem["R"], dtype=float)
        B = np.asarray(problem["B"], dtype=float)
        c = np.asarray(problem["c"], dtype=float)
        T = np.asarray(problem["T"], dtype=float)

        m, n = P.shape
        if R.shape != (m,) or B.shape != (m,) or c.shape != (m,) or T.shape != (n,):
            return {
                "status": "invalid_input_shapes",
                "optimal": False,
            }

        num_D = m * n
        num_vars = num_D + m

        # Objective: minimize -sum(t)
        obj = np.zeros(num_vars, dtype=float)
        obj[num_D:] = -1.0

        # Build A_ub and b_ub in three blocks using vectorized construction.
        # Block 1: Capacity constraints per time t: sum_i D_it <= T_t  (n rows)
        rows_cap = np.repeat(np.arange(n), m)
        cols_cap = np.tile(np.arange(m) * n, n) + np.repeat(np.arange(n), m)
        data_cap = np.ones_like(cols_cap, dtype=float)
        b_cap = T

        # Block 2: Minimum display constraints per ad i: -sum_t D_it <= -c_i  (m rows)
        rows_min = np.repeat(np.arange(m) + n, n)
        cols_min = np.arange(num_D)
        data_min = -np.ones_like(cols_min, dtype=float)
        b_min = -c

        # Block 3: Revenue linking per ad i:
        # t_i - R_i * sum_t P_it * D_it <= 0  (m rows)
        rows_rev_D_all = np.repeat(np.arange(m) + n + m, n)
        coeff_rev_D_all = (-R[:, None] * P).ravel(order="C")
        cols_rev_D_all = np.arange(num_D)
        # Filter out zero coefficients to reduce matrix size
        mask = coeff_rev_D_all != 0.0
        rows_rev_D = rows_rev_D_all[mask]
        cols_rev_D = cols_rev_D_all[mask]
        data_rev_D = coeff_rev_D_all[mask]
        # t-part (diagonal 1's on t variables)
        rows_rev_t = np.arange(m) + n + m
        cols_rev_t = num_D + np.arange(m)
        data_rev_t = np.ones(m, dtype=float)
        b_rev = np.zeros(m, dtype=float)

        # Concatenate all blocks
        rows = np.concatenate([rows_cap, rows_min, rows_rev_D, rows_rev_t])
        cols = np.concatenate([cols_cap, cols_min, cols_rev_D, cols_rev_t])
        data = np.concatenate([data_cap, data_min, data_rev_D, data_rev_t])
        b_ub = np.concatenate([b_cap, b_min, b_rev])

        A_ub = coo_matrix((data, (rows, cols)), shape=(n + m + m, num_vars)).tocsr()

        # Variable bounds
        bounds = []
        # D_it >= 0, no explicit upper bound
        bounds.extend([(0.0, None) for _ in range(num_D)])
        # 0 <= t_i <= B_i (if B_i is finite), else upper bound None
        for i in range(m):
            Bi = float(B[i])
            ub = None if not np.isfinite(Bi) else Bi
            bounds.append((0.0, ub))

        # Solve LP using HiGHS
        res = linprog(c=obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        if not res.success:
            return {
                "status": f"linprog_failed: {res.message}",
                "optimal": False,
            }

        x = res.x
        D_opt = x[:num_D].reshape((m, n))

        # Numerical cleanup: clip tiny negatives to zero
        if np.any(D_opt < 0):
            D_opt = np.maximum(D_opt, 0.0)

        # Compute clicks and revenue
        clicks = np.einsum("ij,ij->i", P, D_opt)
        revenue_per_ad = np.minimum(R * clicks, B)
        total_revenue = float(np.sum(revenue_per_ad))

        return {
            "status": "optimal",
            "optimal": True,
            "displays": D_opt.tolist(),
            "clicks": clicks.tolist(),
            "revenue_per_ad": revenue_per_ad.tolist(),
            "total_revenue": total_revenue,
        }
EOF
