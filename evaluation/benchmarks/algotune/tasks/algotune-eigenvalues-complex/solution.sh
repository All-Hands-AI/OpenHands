#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from numpy.typing import NDArray
from typing import Any

class Solver:
    def solve(self, problem: NDArray, **kwargs) -> Any:
        """
        Solve the eigenvalue problem for the given square matrix.
        The solution returned is a list of eigenvalues sorted in descending order.
        The sorting order is defined as follows: first by the real part (descending),
        then by the imaginary part (descending).

        :param problem: A numpy array representing the real square matrix.
        :return: List of eigenvalues (complex numbers) sorted in descending order.
        """
        # Compute eigenvalues using numpy's eigvals for better performance
        eigenvalues = np.linalg.eigvals(problem)
        # Sort eigenvalues: descending order by real part, then by imaginary part
        indices = np.lexsort((-eigenvalues.imag, -eigenvalues.real))
        return eigenvalues[indices].tolist()
        indices = np.lexsort((-eigenvalues.imag, -eigenvalues.real))
        return eigenvalues[indices].tolist()
EOF
