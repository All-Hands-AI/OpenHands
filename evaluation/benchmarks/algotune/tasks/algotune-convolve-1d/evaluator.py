# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from scipy import signal



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "full"

    def generate_problem(self, n: int = 1, random_seed: int = 1234) -> tuple:
        rng = np.random.default_rng(random_seed)
        a = rng.standard_normal(30 * n)
        b = rng.standard_normal(8 * n)
        return (a, b)

    def solve(self, problem: tuple) -> np.ndarray:
        a, b = problem
        return signal.convolve(a, b, mode=self.mode)

    def is_solution(self, problem: tuple, solution: np.ndarray) -> bool:
        """
        Check if the solution is valid and optimal.

        For this task, a solution is valid if its error is within tolerance compared
        to the optimal solution computed by self.solve().

        :param problem: Tuple containing input arrays a and b.
        :param solution: Proposed convolution result.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        a, b = problem
        reference = signal.convolve(a, b, mode=self.mode)
        tol = 1e-6
        error = np.linalg.norm(solution - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(f"Convolve1D error {error} exceeds tolerance {tol}.")
            return False
        return True