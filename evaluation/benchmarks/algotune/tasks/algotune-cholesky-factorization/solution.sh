#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
import jax
import jax.numpy as jnp
from jax import jit
from scipy.linalg import cholesky

class Solver:
    def solve(self, problem, **kwargs):
        """
        Solve the Cholesky factorization problem by computing the Cholesky decomposition of matrix A.
        Computes A = L L^T where L is lower triangular.
        
        :param problem: A dictionary representing the Cholesky factorization problem.
        :return: A dictionary with key "Cholesky" containing a dictionary with key "L".
        """
        # Convert to numpy array with optimal dtype and memory layout
        A = np.asarray(problem["matrix"], dtype=np.float64, order='C')
        problem["matrix"] = A  # Update the problem dict for validation
        
        # Use scipy's highly optimized cholesky directly
        L = cholesky(A, lower=True, overwrite_a=False, check_finite=False)
            
        return {"Cholesky": {"L": L}}
EOF
