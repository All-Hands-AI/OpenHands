# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import cvxpy as cp
import numpy as np



class Task:
    def __init__(self, **kwargs):
        r"""
        Initialize the lp centering task.

        Find the optimal x which solves

            maximize    c^Tx - \sum_i \log x_i
            subject to  Ax = b

        c is a n-dimensional real-valued vector defining the objective,
        A is a (m x n)-dimensional real-valued matrix for the equality constraint,
        b is a m-dimensional real-valued vector for the equality constraint,
        x is n-dimensional variable.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random lp centering problem with dimensions that scale with n.
        Set the number of inequality constraints (m) to be n // 2.

        :param n: Scaling parameter for the size of the real-valued domain.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the lp centering problem with keys:
                 "c": a numpy array of shape (n,) representing the linear cost in the objective.
                 "A": a numpy array of shape (m, n) representing the linear coefficient in the equality constraint.
                 "b": a numpy array of shape (m,) representing the bound in the equality constraint.
        """
        logging.debug(
            f"Generating lp centering problem with dimensions scaling with n={n} and random_seed={random_seed}"
        )
        np.random.seed(random_seed)

        n = n + 1
        m = n // 2
        A = np.random.rand(m, n)
        p = np.random.rand(n)
        b = A.dot(p)
        c = np.random.rand(n)

        logging.debug(
            f"Generated lp centering problem with dimensions c={c.shape} A={A.shape}, b={b.shape}"
        )
        return {"c": c.tolist(), "A": A.tolist(), "b": b.tolist()}

    def solve(self, problem: dict[str, Any]) -> dict[str, list]:
        """
        Solve the lp centering problem using CVXPY.

        :param problem: A dictionary of the lp centering problem's parameters.
        :return: A dictionary with key:
                 "solution": a 1D list with n elements representing the solution to the lp centering problem.
        """
        c = np.array(problem["c"])
        A = np.array(problem["A"])
        b = np.array(problem["b"])
        n = c.shape[0]

        x = cp.Variable(n)
        prob = cp.Problem(cp.Minimize(c.T @ x - cp.sum(cp.log(x))), [A @ x == b])
        prob.solve(solver="CLARABEL")
        assert prob.status == "optimal"
        return {"solution": x.value.tolist()}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, list]) -> bool:
        """
        Validate the lp centering solution.

        :param problem: A dictionary representing the lp centering problem.
        :param solution: A dictionary containing the proposed solution with key "solution"
        :return: True if the solution is valid and optimal, False otherwise.
        """
        proposed_solution = solution.get("solution")
        if proposed_solution is None:
            logging.error("Problem does not contain 'solution'.")
            return False

        real_solution = self.solve(problem)["solution"]

        if not np.allclose(proposed_solution, real_solution, atol=1e-6):
            logging.error("Proposed solution does not match the real solution within tolerance.")
            return False

        # All checks passed; return a valid float.
        return True