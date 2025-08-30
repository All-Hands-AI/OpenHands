# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from scipy import signal



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Upfirdn1D Task.

        :param kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> list:
        """
        Generate a set of 1D upfirdn problems with random up/down factors.

        For each combination of filter length (fixed at 8) and base signal length,
        the filter h and signal x are generated using a standard normal distribution.
        Additionally, 'up' and 'down' integer factors are randomly chosen from
        [1, 2, 4, 8] for each generated problem.

        :param n: Scaling factor for the signal length.
        :param random_seed: Seed for reproducibility.
        :return: A list of tuples (h, x, up, down).
        """
        rng = np.random.default_rng(random_seed)
        problems = []
        up_choices = [1, 2, 4, 8]
        down_choices = [1, 2, 4, 8]

        for nfilt in [8]:
            for n_signal_base in [32, 128, 512, 2048]:
                n_signal = n_signal_base * n
                if n_signal <= 0:
                    continue

                h = rng.standard_normal(nfilt)
                x = rng.standard_normal(n_signal)
                up = rng.choice(up_choices)
                down = rng.choice(down_choices)

                problems.append((h, x, up, down))
        return problems

    def solve(self, problem: list) -> list:
        """
        Compute the upfirdn operation for each problem definition in the list.

        :param problem: A list of tuples (h, x, up, down).
        :return: A list of 1D arrays representing the upfirdn results.
        """
        results = []
        for h, x, up, down in problem:
            # Use the up/down factors directly from the problem tuple
            res = signal.upfirdn(h, x, up=up, down=down)
            results.append(res)
        return results

    def is_solution(self, problem: list, solution: list) -> bool:
        """
        Check if the upfirdn solution is valid and optimal.

        Compares each result against a reference calculation using the
        specific up/down factors associated with that problem instance.

        :param problem: A list of tuples (h, x, up, down).
        :param solution: A list of 1D arrays of upfirdn results.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        tol = 1e-6
        total_diff = 0.0
        total_ref = 0.0

        if len(problem) != len(solution):
            return False

        for i, (h, x, up, down) in enumerate(problem):
            sol_i = solution[i]
            if sol_i is None:
                # A None in the solution likely indicates a failure during solve
                return False

            # Calculate reference using the up/down factors from the problem tuple
            try:
                ref = signal.upfirdn(h, x, up=up, down=down)
            except Exception:
                # If reference calculation itself fails, cannot validate fairly
                logging.error(f"Reference calculation failed for problem {i}")
                return False

            sol_i_arr = np.asarray(sol_i)

            # Basic sanity check for shape match before calculating norms
            if sol_i_arr.shape != ref.shape:
                logging.error(
                    f"Shape mismatch for problem {i}: Sol={sol_i_arr.shape}, Ref={ref.shape}"
                )
                return False

            try:
                total_diff += np.linalg.norm(sol_i_arr - ref)
                total_ref += np.linalg.norm(ref)
            except Exception:
                # Handle potential errors during norm calculation (e.g., dtype issues)
                logging.error(f"Norm calculation failed for problem {i}")
                return False

        # Avoid division by zero if the total reference norm is effectively zero
        if total_ref < 1e-12:
            # If reference is zero, difference must also be zero (within tolerance)
            return total_diff < tol

        rel_error = total_diff / total_ref
        if rel_error > tol:
            logging.error(
                f"Upfirdn1D aggregated relative error {rel_error} exceeds tolerance {tol}."
            )
            return False

        return True