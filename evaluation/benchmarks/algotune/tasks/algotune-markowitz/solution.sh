#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
import cvxpy as cp

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, list[float]] | None:
        μ = np.asarray(problem["μ"], dtype=np.float64)
        Σ = np.asarray(problem["Σ"], dtype=np.float64)
        γ = float(problem["γ"])
        n = μ.size
        
        w = cp.Variable(n)
        obj = cp.Maximize(μ @ w - γ * cp.quad_form(w, cp.psd_wrap(Σ)))
        cons = [cp.sum(w) == 1, w >= 0]
        
        try:
            prob = cp.Problem(obj, cons)
            prob.solve()
        except cp.error.SolverError:
            return None
        
        if w.value is None or not np.isfinite(w.value).all():
            return None
        
        return {"w": w.value.tolist()}
EOF
