#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix

class Solver:
    def solve(self, problem: dict, **kwargs) -> dict:
        # Extract problem parameters
        T = int(problem["T"])
        p = np.array(problem["p"], dtype=float)
        u = np.array(problem["u"], dtype=float)
        battery = problem["batteries"][0]
        Q = float(battery["Q"])
        C = float(battery["C"])
        D = float(battery["D"])
        eff = float(battery["efficiency"])

        # Number of variables: c_in[0..T-1], c_out[0..T-1], q[0..T-1]
        nvar = 3 * T

        # Objective: minimize p @ (c_in - c_out)
        c_obj = np.zeros(nvar, dtype=float)
        c_obj[0:T] = p
        c_obj[T:2*T] = -p

        # Variable bounds
        bounds = [(0.0, C)] * T + [(0.0, D)] * T + [(0.0, Q)] * T

        # Equality constraints (battery dynamics & cyclic)
        data_eq = []
        row_eq = []
        col_eq = []
        # Dynamics for t = 0..T-2
        for t in range(T - 1):
            # -eff * c_in[t]
            row_eq.append(t); col_eq.append(t); data_eq.append(-eff)
            # + (1/eff) * c_out[t]
            row_eq.append(t); col_eq.append(T + t); data_eq.append(1.0 / eff)
            # -1 * q[t]
            row_eq.append(t); col_eq.append(2*T + t); data_eq.append(-1.0)
            # +1 * q[t+1]
            row_eq.append(t); col_eq.append(2*T + t + 1); data_eq.append(1.0)
        # Cyclic: t = T-1
        t = T - 1
        row_eq.append(t); col_eq.append(t); data_eq.append(-eff)
        row_eq.append(t); col_eq.append(T + t); data_eq.append(1.0 / eff)
        row_eq.append(t); col_eq.append(2*T + t); data_eq.append(-1.0)
        row_eq.append(t); col_eq.append(2*T + 0); data_eq.append(1.0)
        A_eq = coo_matrix((data_eq, (row_eq, col_eq)), shape=(T, nvar))
        b_eq = np.zeros(T, dtype=float)

        # Inequality constraints: -c_in + c_out <= u  (no power back to grid)
        data_ub = []
        row_ub = []
        col_ub = []
        for t in range(T):
            # -1 * c_in[t]
            row_ub.append(t); col_ub.append(t); data_ub.append(-1.0)
            # +1 * c_out[t]
            row_ub.append(t); col_ub.append(T + t); data_ub.append(1.0)
        A_ub = coo_matrix((data_ub, (row_ub, col_ub)), shape=(T, nvar))
        b_ub = u.copy()

        # Solve the linear program using HiGHS via SciPy
        res = linprog(
            c=c_obj,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs-ds",
            options={"presolve": True},
        )
        if not getattr(res, "success", False):
            return {"status": getattr(res, "message", "solver_error"), "optimal": False}

        x = res.x
        c_in_val = x[0:T]
        c_out_val = x[T:2*T]
        q_val = x[2*T:3*T]
        c_net = c_in_val - c_out_val

        # Cost calculations
        cost_without = float(np.dot(p, u))
        cost_with = float(np.dot(p, u + c_net))
        savings = cost_without - cost_with
        savings_percent = 100.0 * savings / cost_without if cost_without != 0 else 0.0

        # Prepare output
        return {
            "status": "optimal",
            "optimal": True,
            "battery_results": [
                {
                    "q": q_val.tolist(),
                    "c": c_net.tolist(),
                    "c_in": c_in_val.tolist(),
                    "c_out": c_out_val.tolist(),
                    "cost": cost_with,
                }
            ],
            "total_charging": c_net.tolist(),
            "cost_without_battery": cost_without,
            "cost_with_battery": cost_with,
            "savings": savings,
            "savings_percent": savings_percent,
        }
EOF
