# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.stats import norm, wasserstein_distance



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the WassersteinDist Task.

        Computes the Wasserstein distance (or earth moving distance) from two discrete distributions. Uses
        `scipy.stats.wasserstein_distance`.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate random distributions using n to control the hardness
        """
        np.random.seed(random_seed)

        x = np.arange(1, 4 * n + 1)

        # Distribution 1: a mixture of 1-2 Gaussians
        centers1 = np.random.choice(x, size=np.random.randint(1, 3), replace=False)
        weights1 = np.random.dirichlet(np.ones(len(centers1)))
        probs1 = sum(w * norm.pdf(x, loc=c, scale=2 * n / 5) for w, c in zip(weights1, centers1))
        mu = probs1 / probs1.sum()

        # Distribution 2: shifted / perturbed version of the first
        centers2 = (centers1 + np.random.randint(3 * n, 4 * n + 1, size=len(centers1))) % n + 1
        weights2 = np.random.dirichlet(np.ones(len(centers2)))
        probs2 = sum(w * norm.pdf(x, loc=c, scale=n) for w, c in zip(weights2, centers2))
        nu = probs2 / probs2.sum()

        return {"u": mu.tolist(), "v": nu.tolist()}

    def solve(self, problem: dict[str, list[float]]) -> float:
        """
        Solves the wasserstein distance using scipy.stats.wasserstein_distance.

        :param problem: a Dict containing info for dist u and v
        :return: A float determine the wasserstein distance
        """

        try:
            n = len(problem["u"])
            d = wasserstein_distance(
                list(range(1, n + 1)), list(range(1, n + 1)), problem["u"], problem["v"]
            )
            return d
        except Exception as e:
            logging.error(f"Error: {e}")
            return float(len(problem["u"]))

    def is_solution(self, problem: dict[str, list[float]], solution: float) -> bool:
        try:
            tol = 1e-5
            d = self.solve(problem)
            if solution > d + tol:
                return False
            elif solution < d - tol:
                return False
            else:
                return True
        except Exception as e:
            logging.error(f"Error when verifying solution: {e}")
            return False