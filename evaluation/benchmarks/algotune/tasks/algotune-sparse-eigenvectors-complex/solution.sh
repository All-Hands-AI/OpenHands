#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, List

import numpy as np
from scipy import sparse

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> List[np.ndarray]:
        """
        Compute the eigenvectors corresponding to the k eigenvalues of largest magnitude
        for a given sparse square matrix, and return them sorted in descending order
        by the modulus of their associated eigenvalues.

        Mirrors the reference solver's ARPACK parameters to ensure deterministic
        alignment with validation, while using a stable NumPy-based ordering.
        """
        A = problem["matrix"]
        k = int(problem["k"])
        n = A.shape[0]

        # Deterministic starting vector using matrix dtype (matches validator)
        v0 = np.ones(n, dtype=A.dtype)

        # Use ARPACK (eigs) with same parameters as validator to ensure alignment
        eigenvalues, eigenvectors = sparse.linalg.eigs(
            A,
            k=k,
            v0=v0,
            maxiter=n * 200,
            ncv=max(2 * k + 1, 20),
        )

        # Stable order by descending magnitude of eigenvalues using mergesort
        order = np.argsort(-np.abs(eigenvalues), kind="mergesort")

        # Return as list of 1D arrays (each eigenvector is a column)
        return [eigenvectors[:, idx] for idx in order[:k]]
EOF
