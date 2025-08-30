#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
from scipy.optimize import linprog

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, list]:
        """
        Solve the Chebyshev center problem using scipy.optimize with optimized settings.
        
        :param problem: A dictionary of the Chebyshev center problem's parameters.
        :return: A dictionary with key:
                 "solution": a 1D list with n elements representing the solution to the Chebyshev center problem.
        """
        # Convert to numpy arrays for efficiency
        a = np.asarray(problem["a"], dtype=np.float64)
        b = np.asarray(problem["b"], dtype=np.float64)
        n = a.shape[1]
        m = a.shape[0]
        
        # Pre-allocate arrays
        a_norms = np.empty(m, dtype=np.float64)
        A_ub = np.empty((m, n + 1), dtype=np.float64, order='C')
        c = np.empty(n + 1, dtype=np.float64)
        bounds = [(None, None)] * n + [(0, None)]
        
        # Compute norms using faster method
        np.sqrt(np.sum(a * a, axis=1), out=a_norms)
        
        # Build constraint matrix more efficiently
        A_ub[:, :-1] = a
        A_ub[:, -1] = a_norms
        
        # Objective: minimize -r (maximize r)
        c.fill(0.0)
        c[-1] = -1.0
        
        # Solve with interior-point method for speed
        result = linprog(
            c, 
            A_ub=A_ub, 
            b_ub=b, 
            bounds=bounds, 
            method='interior-point',
            options={'presolve': True, 'tol': 1e-9}
        )
        
        # Always return the solution, even if not marked as success
        return {"solution": result.x[:-1].tolist()}
EOF
