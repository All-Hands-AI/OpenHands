# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import numpy as np



class Task:
    def __init__(self, **kwargs):
        """
        Initialize l1_pruning task. Solving an L1 proximal operator or projecting a point onto L1 ball involves the following optimization problem:
            min_w ‖v-w‖² s.t. ‖w‖₁ ≤ k
        where
            v is the given vector of n real numbers
            ‖.‖  is an l2 norm
            ‖θ‖₁ is an l1 norm, i.e. sum of absolute values of a vector;
            k    is a user-defined constant
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random real-valued vector of dimension n and a random value for hyperparameter k.

        :param n: Scaling parameter for the size of the real-valued domain.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the problem with keys:
                 "v": A list of n numbers representing the vector v,
                 "k": A hyperparameter (integer) that controls pruning severity for v.
        """
        logging.debug(
            f"Generating l1_pruning with dimensions scaling with n={n} and random_seed={random_seed}"
        )
        random.seed(random_seed)
        np.random.seed(random_seed)

        v = np.random.randn(n)
        k = random.randint(1, max(1, n // 2))  # Randomly choose k between 1 and n/2

        problem = {"v": v.tolist(), "k": k}
        logging.debug(f"Generated l1_pruning v={v.shape} and k={k}")
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, list]:
        """
        Solve the problem using the algorithm described in https://doi.org/10.1109/CVPR.2018.00890.

        This optimization problem is a Quadratic Program (QP).
        However, it can be solved exactly in O(nlogn).

        :param problem: A dictionary of the problem's parameters.
        :return: A dictionary with key:
                 "solution": a 1D list with n elements representing the solution to the l1_pruning task.
        """
        v = np.array(problem.get("v"))
        k = problem.get("k")

        # Ensure v is a column vector
        v = v.flatten()

        def subproblem_sol(vn, z):
            mu = np.sort(vn, kind="mergesort")[::-1]
            cumsum = 0
            theta = 0
            for j in range(len(mu)):
                cumsum += mu[j]
                if mu[j] < 1 / (j + 1) * (cumsum - z):
                    theta = 1 / (j + 1) * (cumsum - z)
                    break
            w = np.maximum(vn - theta, 0)
            return w

        u = np.abs(v)
        b = subproblem_sol(u, k)
        new_v = b * np.sign(v)
        remaining_indx = new_v != 0
        pruned = np.zeros_like(v)
        pruned[remaining_indx] = new_v[remaining_indx]

        solution = {"solution": pruned.tolist()}
        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, list]) -> float:
        """
        Validate the solution to the l1_pruning problem.

        :param problem: A dictionary representing the problem.
        :param solution: A dictionary containing the proposed solution with key "solution"
        :return: True if solution is valid and optimal, False otherwise.
        """
        proposed_solution = solution.get("solution")
        if proposed_solution is None:
            logging.error("Problem does not contain 'solution'.")
            return False

        real_solution = self.solve(problem).get("solution")

        if not np.allclose(proposed_solution, real_solution, atol=1e-6):
            logging.error(
                "Proposed solution does not match the ground-truth solution within tolerance."
            )
            return False

        # All checks passed; return True
        return True