# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import cumulative_simpson



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int = 1000, random_seed: int = 1, k_max: int = 4) -> dict:
        """
        Generate a richer signal: sum_{k=1..K} a_k sin(2π k x + φ_k) with random
        coefficients.  K (=k_max) can be kept small so the integral remains smooth.
        """
        rng = np.random.default_rng(random_seed)
        x, dx = np.linspace(0, 5, n, retstep=True)

        ks     = rng.integers(1, k_max + 1, size=k_max)      # frequencies
        amps   = rng.uniform(0.3, 1.0,   size=k_max)         # amplitudes
        phases = rng.uniform(0, 2 * np.pi, size=k_max)       # phases

        y = sum(A * np.sin(2 * np.pi * k * x + φ)
                for A, k, φ in zip(amps, ks, phases))
        return {"y": y, "dx": dx}

    def solve(self, problem: dict) -> NDArray:
        """
        Compute the cumulative integral of the 1D array using Simpson's rule.
        """
        y = problem["y"]
        dx = problem["dx"]
        result = cumulative_simpson(y, dx=dx)
        return result

    def is_solution(self, problem: dict, solution: NDArray) -> bool:
        """
        Check if the cumulative Simpson solution is valid and optimal.

        A valid solution must match the reference implementation (scipy's cumulative_simpson)
        within a small tolerance.

        :param problem: A dictionary containing the input array and dx.
        :param solution: The computed cumulative integral.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        y = problem["y"]
        dx = problem["dx"]
        reference = cumulative_simpson(y, dx=dx)
        tol = 1e-6
        error = np.linalg.norm(solution - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(f"Cumulative Simpson 1D relative error {error} exceeds tolerance {tol}.")
            return False
        return True