#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict
import numpy as np
import cvxpy as cp

class Solver:
    def solve(self, problem: Dict[str, Any]) -> Dict[str, list]:
        # Unpack data
        c = np.array(problem["c"], dtype=float)
        A = np.array(problem["A"], dtype=float)
        b = np.array(problem["b"], dtype=float)
        n = c.shape[0]

        # Define optimization variable
        x = cp.Variable(n)

        # Form objective: maximize c^T x - sum(log x) => minimize negative
        objective = cp.Minimize(c.T @ x - cp.sum(cp.log(x)))

        # Equality constraint
        constraints = [A @ x == b]

        # Solve using CLARABEL (interior-point)
        prob = cp.Problem(objective, constraints)
        prob.solve(solver="CLARABEL")

        if prob.status not in [cp.OPTIMAL, "optimal"]:
            raise RuntimeError(f"CVXPY failed with status {prob.status}")

        return {"solution": x.value.tolist()}
EOF
