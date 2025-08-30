# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from sklearn import linear_model



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Lasso Task.

        Finds the coefficients of features given the data matrix X and the labels y. Uses
        `sklearn.linear_model.Lasso`.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate random data matrix using n to control the hardness
        """
        np.random.seed(random_seed)
        d = 10 * n  # number of features
        m = 5 * n  # number of samples
        s = n  # sparsity level

        # Step 1: Generate design matrix X
        X = np.random.randn(m, d)

        # Step 2: Generate sparse true beta
        beta_true = np.zeros(d)
        idx = np.random.choice(d, s, replace=False)
        beta_true[idx] = np.random.randn(s)

        # Step 3: Generate target y with small noise
        y = X @ beta_true + 0.01 * np.random.randn(m)

        # Return NumPy arrays directly so that the dataset writer can
        # detect large ndarrays and externalise them to .npy files
        # instead of embedding gigabytes of JSON.  Down-stream code
        # (solve / is_solution) already converts to NumPy via
        # np.array(...), so nothing else needs to change.
        return {"X": X, "y": y}

    def solve(self, problem: dict[str, Any]) -> list[float]:
        try:
            # use sklearn.linear_model.Lasso to solve the task
            clf = linear_model.Lasso(alpha=0.1, fit_intercept=False)
            clf.fit(problem["X"], problem["y"])
            return clf.coef_.tolist()
        except Exception as e:
            logging.error(f"Error: {e}")
            _, d = problem["X"].shape
            return np.zeros(d).tolist()  # return trivial answer

    def is_solution(self, problem: dict[str, Any], solution: list[float]) -> bool:
        try:
            tol = 1e-5
            w = np.array(self.solve(problem)).reshape(-1, 1)
            w_sol = np.array(solution).reshape(-1, 1)
            X = np.array(problem["X"])
            y = np.array(problem["y"]).reshape(-1, 1)
            n, _ = X.shape
            error_solver = 1 / (2 * n) * np.sum((y - X @ w) ** 2) + 0.1 * np.sum(np.abs(w))
            error_sol = 1 / (2 * n) * np.sum((y - X @ w_sol) ** 2) + 0.1 * np.sum(np.abs(w_sol))
            if error_sol > error_solver + tol:
                return False
            else:
                return True
        except Exception as e:
            logging.error(f"Error when verifying solution: {e}")
            return False