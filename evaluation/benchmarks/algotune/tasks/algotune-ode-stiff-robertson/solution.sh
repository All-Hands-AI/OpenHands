#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy.integrate import odeint
from numba import jit

@jit(nopython=True, fastmath=True)
def rober(y, t, k1, k2, k3):
    y1, y2, y3 = y
    f0 = -k1 * y1 + k3 * y2 * y3
    f1 = k1 * y1 - k2 * y2**2 - k3 * y2 * y3
    f2 = k2 * y2**2
    return np.array([f0, f1, f2])

@jit(nopython=True, fastmath=True)
def jac(y, t, k1, k2, k3):
    y1, y2, y3 = y
    return np.array([
        [-k1, k3 * y3, k3 * y2],
        [k1, -2*k2*y2 - k3*y3, -k3*y2],
        [0, 2*k2*y2, 0]
    ])

class Solver:
    def solve(self, problem, **kwargs):
        y0 = np.array(problem["y0"])
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        k = problem["k"]
        k1, k2, k3 = k
        
        # Precompile the functions with sample inputs
        _ = rober(y0, 0.0, k1, k2, k3)
        _ = jac(y0, 0.0, k1, k2, k3)
        
        # Solve the ODE system with Jacobian
        sol = odeint(
            rober,
            y0,
            np.array([t0, t1]),
            args=(k1, k2, k3),
            Dfun=jac,
            rtol=1e-7,
            atol=1e-9,
            mxstep=10000
        )
        
        return sol[-1].tolist()
EOF
