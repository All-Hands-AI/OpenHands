# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random

import numpy as np
import scipy.linalg as la
from numpy.typing import NDArray



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the GeneralizedEigenvaluesComplex task.

        In this task, you are given two matrices A and B, where:
          - A and B are arbitrary real n x n matrices.
        The goal is to solve the generalized eigenvalue problem:

            A · x = λ B · x

        The eigenvalues are not necessarily real (i.e., they may be complex).
        The solution should return a list of eigenvalues sorted in descending order.
        The sorting order is defined as: first by the real part (descending),
        then by the imaginary part (descending).
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> tuple[NDArray, NDArray]:
        """
        Generate a random generalized eigenvalue problem with potentially complex eigenvalues.

        Two matrices A and B of size n x n are generated:
          - A is generated as a random non-symmetric matrix with controlled singular values.
          - B is generated as a random invertible matrix, also with controlled singular values.

        :param n: Dimension of the matrices.
        :param random_seed: Seed for reproducibility.
        :return: Tuple (A, B) where A and B are real n x n matrices.
        """
        logging.debug(
            f"Generating generalized eigenvalue complex problem with n={n} and random_seed={random_seed}"
        )
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Generate matrix A with controlled singular values
        Q1, _ = np.linalg.qr(np.random.randn(n, n))
        Q2, _ = np.linalg.qr(np.random.randn(n, n))
        # Create diagonal matrix with well-spaced singular values
        D = np.diag(0.1 + 0.9 * np.random.rand(n))
        A = Q1 @ D @ Q2.T  # Ensures A has controlled singular values

        # Generate invertible matrix B with controlled condition number
        Q3, _ = np.linalg.qr(np.random.randn(n, n))
        Q4, _ = np.linalg.qr(np.random.randn(n, n))
        # Create diagonal matrix with well-spaced singular values > 1
        D2 = np.diag(1.0 + np.random.rand(n))
        B = Q3 @ D2 @ Q4.T  # Ensures B is invertible with singular values in [1,2]

        logging.debug(
            f"Generated matrices A and B of size {n}x{n} for the generalized eigenvalue complex problem."
        )
        return (A, B)

    def solve(self, problem: tuple[NDArray, NDArray]) -> list[complex]:
        """
        Solve the generalized eigenvalue problem for the given matrices A and B.

        The problem is defined as: A · x = λ B · x.
        For better numerical stability, we first scale B, then solve the problem.

        The solution is a list of eigenvalues sorted in descending order, where the sorting order
        is defined as: first by the real part (descending), then by the imaginary part (descending).

        :param problem: Tuple (A, B) where A and B are n x n real matrices.
        :return: List of eigenvalues (complex numbers) sorted in descending order.
        """
        A, B = problem
        logging.debug("Starting generalized eigenvalue computation using scipy.linalg.eig.")

        # Scale matrices for better numerical stability.
        scale_B = np.sqrt(np.linalg.norm(B))
        B_scaled = B / scale_B
        A_scaled = A / scale_B

        # Solve scaled problem.
        eigenvalues, _ = la.eig(A_scaled, B_scaled)

        # Sort eigenvalues: descending order by real part, then by imaginary part.
        solution = sorted(eigenvalues, key=lambda x: (-x.real, -x.imag))
        logging.debug(f"Computed generalized eigenvalues (sorted in descending order): {solution}")
        return solution

    def is_solution(self, problem: tuple[NDArray, NDArray], solution: list[complex]) -> bool:
        """
        Check if the generalized eigenvalue solution is valid and optimal.

        Checks performed:
          1. The solution is a list of complex numbers with length n.
          2. Each eigenvalue is finite.
          3. Eigenvalues are sorted in descending order by re-sorting with the same key
             and confirming they match the user-provided list.
          4. For each eigenvalue λ, check that (A - λ B) is nearly singular. We compute the
             smallest singular value of (A - λ B). The relative error is:
                 min_sigma / (||A|| + ||B|| + ε),
             which must be below a specified tolerance.

        :param problem: Tuple (A, B) where A and B are n x n real matrices.
        :param solution: List of eigenvalues (complex numbers) purportedly sorted in descending order.
        :return: True if the solution is valid and optimal; otherwise, False.
        """
        A, B = problem
        n = A.shape[0]
        tol = 1e-6
        epsilon = 1e-12

        # 1. Check that solution is a list of length n.
        if not isinstance(solution, list):
            logging.error("Solution is not a list.")
            return False
        if len(solution) != n:
            logging.error(f"Solution length {len(solution)} does not match expected size {n}.")
            return False

        # 2. Check that each eigenvalue is a finite complex number.
        for i, eig in enumerate(solution):
            try:
                lam = complex(eig)
            except Exception as e:
                logging.error(f"Eigenvalue at index {i} cannot be converted to complex: {e}")
                return False
            if not (np.isfinite(lam.real) and np.isfinite(lam.imag)):
                logging.error(f"Eigenvalue at index {i} is not finite: {lam}")
                return False

        # 3. Verify the user-provided list is sorted in descending order
        #    by re-sorting with the exact same key.
        sorted_solution = sorted(solution, key=lambda x: (-x.real, -x.imag))

        # Compare element by element to ensure they match (within a small tolerance).
        for cand, sorted_val in zip(solution, sorted_solution):
            # If they differ significantly, the user's solution isn't sorted properly.
            if abs(cand - sorted_val) > 1e-12:
                logging.error("Eigenvalues are not sorted in descending order.")
                return False

        # 4. For each eigenvalue, check if A - λ B is nearly singular.
        norm_A = np.linalg.norm(A)
        norm_B = np.linalg.norm(B)

        for i, lam in enumerate(solution):
            residual_matrix = A - lam * B
            # Compute smallest singular value of (A - λ B).
            try:
                singular_values = np.linalg.svd(residual_matrix, compute_uv=False)
            except Exception as e:
                logging.error(f"Error computing SVD for eigenvalue index {i}: {e}")
                return False
            min_sv = np.min(np.abs(singular_values))

            # If (A - λ B) is truly singular, min_sv should be near zero.
            rel_error = min_sv / (norm_A + norm_B + epsilon)
            if rel_error > tol:
                logging.error(
                    f"Eigenvalue at index {i} has relative residual error {rel_error} "
                    f"which exceeds tolerance {tol}."
                )
                return False

        return True