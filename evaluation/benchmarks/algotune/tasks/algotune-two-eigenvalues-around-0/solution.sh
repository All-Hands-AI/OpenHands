#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np  
from scipy.linalg import lu_factor, lu_solve  
from scipy.sparse.linalg import eigsh, LinearOperator  
  
class Solver:  
    def solve(self, problem, **kwargs):  
        """Find the two eigenvalues of a symmetric matrix closest to zero."""  
        # Load matrix as Fortran-order for faster LU  
        A = np.array(problem["matrix"], dtype=float, order='F')  
        n = A.shape[0]  
        # Use ARPACK shift-invert for large matrices  
        if n > 200:  
            # LU factorization in-place  
            lu, piv = lu_factor(A, overwrite_a=True)  
            # Define inverse matvec via LU solve  
            def mv(x):  
                return lu_solve((lu, piv), x)  
            A_inv = LinearOperator((n, n), matvec=mv, dtype=float)  
            # Compute two largest eigenvalues of A_inv => two smallest of A  
            inv_vals = eigsh(A_inv, k=2, which='LM', tol=1e-4, ncv=8, return_eigenvectors=False)  
            vals = 1.0 / inv_vals  
            # Sort by absolute value  
            idx = np.argsort(np.abs(vals))  
            return [float(vals[idx[0]]), float(vals[idx[1]])]  
        # Fallback: full dense solve using LAPACK DSYEVH  
        vals = np.linalg.eigvalsh(A)  
        # Find two entries with smallest absolute value  
        idx = np.argpartition(np.abs(vals), 2)[:2]  
        v0, v1 = vals[idx[0]], vals[idx[1]]  
        if abs(v0) <= abs(v1):  
            return [float(v0), float(v1)]  
        else:  
            return [float(v1), float(v0)]
EOF
