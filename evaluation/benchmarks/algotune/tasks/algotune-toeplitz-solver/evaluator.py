# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from scipy.linalg import matmul_toeplitz, solve_toeplitz



class Task:
    """
    ToeplitzSolver Task:

    Given a square Toeplitz matrix T and a vector b, the task is to solve the linear system Tx = b.
    This task uses the Levinson-Durbin algorithm (scipy.linalg.solve_toeplitz) that is faster than normal linear system solve by taking advantage of the Toeplitz structure.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, list[float]]:
        """
        Generate random row and column arrays of size n, and vector b of size n.

        :param n: The number of rows and columns of the matrix T.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the Toeplitz solver problem with keys:
            "c": A list of length (n) representing the first column of the matrix T.
            "r": A list of length (n) representing the first row of the matrix T.
            "b": A list of length (n) representing the right-hand side vector b.
        """
        logging.debug(
            f"Generating Toeplitz system problem with n={n} and random_seed={random_seed}"
        )
        rng = np.random.default_rng(random_seed)

        c = rng.standard_normal(n)
        r = rng.standard_normal(n)
        # Ensure main diagonal is non-zero (with magnitude increasing as n grows, to make matrix well conditioned for the less numerically stable levinson algo)
        diag = np.abs(c[0]) + np.sqrt(n)
        sign = np.sign(c[0])
        r[0] = sign * diag
        c[0] = sign * diag
        b = rng.standard_normal(n)
        return {"c": c.tolist(), "r": r.tolist(), "b": b.tolist()}

    def solve(self, problem: dict[str, list[float]]) -> list[float]:
        """
        Solve the linear system Tx = b using scipy solve_Toeplitz.

        :param problem: A dictionary representing the Toeplitz system problem.
        :return: A list of numbers representing the solution vector x.
        """
        c = np.array(problem["c"])
        r = np.array(problem["r"])
        b = np.array(problem["b"])

        x = solve_toeplitz((c, r), b)
        return x.tolist()

    def is_solution(self, problem: dict[str, list[float]], solution: list[float]) -> bool:
        """

        Check if the provided solution is valid and optimal for the linear system Tx = b.

        This method checks:
          - The solution vector x has the correct dimension.
          - All outputs contain only finite values (no infinities or NaNs).
          - The equation Tx = b is satisfied within a small tolerance.

        For linear systems with a unique solution, there is only one optimal solution.

        :param problem: A dictionary containing the problem with keys "c", "r", and "b" as input vectors.
        :param solution: A list of floats representing the proposed solution x.
        :return: True if solution is valid and optimal, False otherwise.
        """

        c = np.array(problem["c"])
        r = np.array(problem["r"])
        b = np.array(problem["b"])

        try:
            x = np.array(solution)
        except Exception as e:
            logging.error(f"Error converting solution list to numpy arrays: {e}")
            return False

        # Check if the solution has the correct dimension
        if x.shape != b.shape:
            return False

        if not np.all(np.isfinite(x)):
            logging.error("Solution contains non-finite values (inf or NaN).")
            return False

        # Check if Tx = b within tolerance.

        Tx = matmul_toeplitz((c, r), x)

        if not np.allclose(Tx, b, atol=1e-6):
            logging.error("Solution is not optimal within tolerance.")
            return False

        return True