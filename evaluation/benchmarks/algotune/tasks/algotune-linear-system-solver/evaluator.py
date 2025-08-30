# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np



def generate_invertible_matrix(
    n: int, random_seed: int = 1
) -> tuple[list[list[float]], list[float]]:
    """
    Generate a random invertible matrix A and a vector b for solving Ax = b.

    The matrix A is constructed using QR decomposition to ensure invertibility.
    The diagonal entries of R are adjusted to have a magnitude of at least 1.0,
    which controls the matrix conditioning.
    """
    np.random.seed(random_seed)
    # Generate a random n x n matrix and compute its QR decomposition.
    Q, R = np.linalg.qr(np.random.randn(n, n))
    # Ensure diagonal entries are non-zero (with magnitude at least 1.0)
    diag = np.abs(np.diag(R)) + 1.0
    R[np.diag_indices(n)] = np.sign(np.diag(R)) * diag
    A = Q @ R
    # Generate a random right-hand side vector b.
    b = np.random.randn(n)
    return A.tolist(), b.tolist()


class Task:
    """
    LinearSystemSolver Task:

    Given a square matrix A and a vector b, the task is to solve the linear system Ax = b.
    This task uses an efficient solver (np.linalg.solve) that avoids explicit matrix inversion.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random, invertible matrix A of size n x n and a vector b.

        Args:
            n (int): The size of the square matrix A.
            random_seed (int): Seed for reproducibility.

        Returns:
            dict: A dictionary with keys:
                  "A": A list of n lists of numbers representing an invertible n x n matrix.
                  "b": A list of n numbers representing the right-hand side vector.
        """
        logging.debug(f"Generating linear system problem with n={n}, random_seed={random_seed}")
        A, b = generate_invertible_matrix(n, random_seed)
        return {"A": A, "b": b}

    def solve(self, problem: dict[str, Any]) -> list[float]:
        """
        Solve the linear system Ax = b using NumPy's optimized solver.

        Args:
            problem (dict): A dictionary with keys "A" and "b".

        Returns:
            list: A list of numbers representing the solution vector x.
        """
        A = np.array(problem["A"])
        b = np.array(problem["b"])
        # np.linalg.solve avoids explicit inversion and is more efficient.
        x = np.linalg.solve(A, b)
        return x.tolist()

    def is_solution(self, problem: dict[str, Any], solution: list[float]) -> bool:
        """
        Check if the provided solution is valid and optimal for the linear system Ax = b.

        A valid solution must satisfy:
        1. The solution vector x has the correct dimension
        2. The equation Ax = b is satisfied within a small tolerance

        For linear systems with a unique solution, there is only one optimal solution.

        Args:
            problem (Dict[str, Any]): A dictionary with keys "A" and "b".
            solution (List[float]): The proposed solution vector x.

        Returns:
            bool: True if the solution is valid and optimal, False otherwise.
        """
        A = np.array(problem["A"])
        b = np.array(problem["b"])

        # Check if the solution has the correct dimension
        if len(solution) != len(b):
            return False

        # Convert solution to numpy array
        x = np.array(solution)

        # Compute residual: ||Ax - b||
        residual = np.linalg.norm(A @ x - b)

        # Check if residual is small enough (solution satisfies Ax = b)
        tol = 1e-6
        return bool(residual <= tol * (1 + np.linalg.norm(b)))