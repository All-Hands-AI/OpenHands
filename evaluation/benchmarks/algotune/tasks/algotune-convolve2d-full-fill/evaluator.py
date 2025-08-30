# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from scipy import signal



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Convolve2DFullFill Task.
        """
        super().__init__(**kwargs)
        self.mode = "full"
        self.boundary = "fill"

    def generate_problem(self, n: int = 1, random_seed: int = 1234) -> tuple:
        """
        Generate a 2D convolution problem.

        The problem consists of a pair of 2D arrays:
          - The first array has shape (30*n, 30*n).
          - The second array has shape (8*n, 8*n).
        These arrays are generated using a random number generator with the given seed.
        As n increases, the arrays become larger and the convolution becomes more computationally intensive.

        :param n: Scaling factor for the array dimensions.
        :param random_seed: Seed for reproducibility.
        :return: A tuple (a, b) of 2D arrays.
        """
        rng = np.random.default_rng(random_seed)
        a = rng.standard_normal((30 * n, 30 * n))
        b = rng.standard_normal((8 * n, 8 * n))
        return (a, b)

    def solve(self, problem: tuple) -> np.ndarray:
        """
        Compute the 2D convolution of arrays a and b using "full" mode and "fill" boundary.

        :param problem: A tuple (a, b) of 2D arrays.
        :return: A 2D array containing the convolution result.
        """
        a, b = problem
        result = signal.convolve2d(a, b, mode=self.mode, boundary=self.boundary)
        return result

    def is_solution(self, problem: tuple, solution: np.ndarray) -> bool:
        """
        Check if the 2D convolution solution is valid and optimal.

        A valid solution must match the reference implementation (signal.convolve2d)
        with "full" mode and "fill" boundary, within a small tolerance.

        :param problem: A tuple (a, b) of 2D arrays.
        :param solution: The computed convolution result.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        a, b = problem
        reference = signal.convolve2d(a, b, mode=self.mode, boundary=self.boundary)
        tol = 1e-6
        error = np.linalg.norm(solution - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(f"Convolve2D solution error {error} exceeds tolerance {tol}.")
            return False
        return True