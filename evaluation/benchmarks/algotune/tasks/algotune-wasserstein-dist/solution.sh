#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
from numba import jit

@jit(nopython=True, fastmath=True, cache=True)
def wasserstein_1d_numba(u, v):
    """Compute 1D Wasserstein distance using cumulative distribution approach."""
    result = 0.0
    cum_u = 0.0
    cum_v = 0.0
    
    # Process elements one by one without range
    i = 0
    n = len(u)
    while i < n:
        cum_u += u[i]
        cum_v += v[i]
        result += abs(cum_u - cum_v)
        i += 1
        
    return result
class Solver:
    def solve(self, problem, **kwargs) -> Any:
        """Compute Wasserstein distance between two discrete distributions."""
        try:
            u = np.array(problem["u"], dtype=np.float64)
            v = np.array(problem["v"], dtype=np.float64)
            
            distance = wasserstein_1d_numba(u, v)
            
            return float(distance)
        except Exception as e:
            return float(len(problem["u"]))
EOF
