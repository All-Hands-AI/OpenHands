# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from itertools import product

import numpy as np
from scipy import signal



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Correlate1D Task.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.mode = "full"

    def generate_problem(self, n: int = 1, random_seed: int = 1234) -> list:
        """
        Generate a list of 1D array pairs for correlation.

        For each pair of lengths (ma, nb) chosen from
        (1, 2, 8, 13, 30, 36, 50, 75), two 1D arrays are generated using a standard normal distribution.
        The sizes of the arrays scale with the parameter n.

        :param n: Scaling factor for the array lengths.
        :param random_seed: Seed for reproducibility.
        :return: A list of tuples, each containing two 1D arrays.
        """
        rng = np.random.default_rng(random_seed)
        pairs = []
        for ma, nb in product((1, 2, 8, 13, 30, 36, 50, 75), repeat=2):
            a = rng.standard_normal(ma * n)
            b = rng.standard_normal(nb * n)
            pairs.append((a, b))
        return pairs

    def solve(self, problem: list) -> list:
        """
        Compute the 1D correlation for each valid pair in the problem list.

        For mode 'valid', process only pairs where the length of the second array does not exceed the first.
        Return a list of 1D arrays representing the correlation results.

        :param problem: A list of tuples of 1D arrays.
        :return: A list of 1D correlation results.
        """
        results = []
        for a, b in problem:
            if self.mode == "valid" and b.shape[0] > a.shape[0]:
                continue
            res = signal.correlate(a, b, mode=self.mode)
            results.append(res)
        return results

    def is_solution(self, problem: list, solution: list) -> bool:
        """
        Check if the 1D correlation solution is valid and optimal.

        A valid solution must:
        1. Have the correct number of results (one for each valid pair)
        2. Match the reference results within a small tolerance

        :param problem: A list of tuples of 1D arrays.
        :param solution: A list of 1D correlation results.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        tol = 1e-6
        total_diff = 0.0
        total_ref = 0.0
        valid_pairs = []
        for a, b in problem:
            valid_pairs.append((a, b))
        if len(valid_pairs) != len(solution):
            logging.error("Number of valid pairs does not match number of solution results.")
            return False
        for i, (a, b) in enumerate(valid_pairs):
            ref = signal.correlate(a, b, mode=self.mode)
            total_diff += np.linalg.norm(solution[i] - ref)
            total_ref += np.linalg.norm(ref)
        rel_error = total_diff / (total_ref + 1e-12)
        if rel_error > tol:
            logging.error(
                f"Correlate1D aggregated relative error {rel_error} exceeds tolerance {tol}."
            )
            return False
        return True