# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import cumulative_simpson



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int = 1000, random_seed: int = 1) -> dict:
        """
        Generate a (100, 100, n) array whose last axis is sampled on a uniform grid
        over [0, 5] but whose amplitude and phase vary per (i, j) “pixel”.

        The random seed controls two (100×100) arrays:
        • `A`   – amplitudes in [0.5, 1.5]  
        • `phi` – phases in [0, 2π)

        y2[i, j, k] = A[i, j] * sin(2π x[k] + phi[i, j])
        """
        rng = np.random.default_rng(random_seed)

        x, dx = np.linspace(0, 5, n, retstep=True)      # 1‑D grid
        x = x[None, None, :]                            # shape (1,1,n) for broadcasting

        A   = rng.uniform(0.5, 1.5,  size=(100, 100, 1))        # amplitudes
        phi = rng.uniform(0, 2 * np.pi, size=(100, 100, 1))     # phases

        y2 = A * np.sin(2 * np.pi * x + phi)            # broadcast multiply/add
        return {"y2": y2, "dx": dx}

    def solve(self, problem: dict) -> NDArray:
        """
        Compute the cumulative integral along the last axis of the multi-dimensional array using Simpson's rule.
        """
        y2 = problem["y2"]
        dx = problem["dx"]
        result = cumulative_simpson(y2, dx=dx)
        return result

    def is_solution(self, problem: dict, solution: NDArray) -> bool:
        """
        Check if the multi-dimensional cumulative Simpson solution is valid and optimal.

        A valid solution must match the reference implementation (scipy's cumulative_simpson)
        within a small tolerance.

        :param problem: A dictionary containing the multi-dimensional input array and dx.
        :param solution: The computed cumulative integral.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        y2 = problem["y2"]
        dx = problem["dx"]
        reference = cumulative_simpson(y2, dx=dx)
        tol = 1e-6
        error = np.linalg.norm(solution - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(
                f"Cumulative Simpson MultiD relative error {error} exceeds tolerance {tol}."
            )
            return False
        return True