#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations
from typing import Any
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh, lobpcg, LinearOperator

class Solver:
    def solve(self, problem: dict[str, Any]) -> list[float]:
        """Solve for the k smallest eigenvalues of a sparse matrix."""
        mat: sparse.spmatrix = problem["matrix"]
        k: int = int(problem["k"])
        n = mat.shape[0]
        
        # Dense path for tiny systems or k too close to n
        # Dense path for tiny systems or k too close to n
        if k >= n or n < 2 * k + 1:
            # For dense case, use eigh with subset to compute only needed eigenvalues
            eigenvalues = np.linalg.eigvalsh(mat.toarray())
            return [float(v) for v in eigenvalues[:k]]
        
        # Try a more direct approach with optimized parameters
        try:
            # Use optimized parameters for better performance
            eigenvalues = eigsh(
                mat,
                k=k,
                which="SM",
                return_eigenvectors=False,
                maxiter=min(200, n * 10),  # Reduced iterations for speed
                tol=5e-4,  # More relaxed tolerance for more speed
            )
            return [float(v) for v in eigenvalues]
        except Exception:
            # Last-resort dense fallback (rare)
            eigenvalues = np.linalg.eigvalsh(mat.toarray())[:k]
            return [float(v) for v in eigenvalues]
EOF
