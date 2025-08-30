# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
import sklearn



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the KMeans Task.

        Finds the assigned clusters of a list of data. Uses
        `sklearn.cluster.KMeans`.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate random data matrix using n to control the hardness
        """
        np.random.seed(random_seed)
        d = 10
        k = n  # number of clusters
        s = 20  # samples per cluster
        X = []

        # Control difficulty via smaller inter-cluster distance & larger intra-cluster spread
        cluster_std = 1.0 + 0.2 * n
        center_spread = 10.0 / n

        centers = np.random.randn(k, d) * center_spread

        for i in range(k):
            cluster_points = np.random.randn(s, d) * cluster_std + centers[i]
            X.append(cluster_points)

        X = np.vstack(X)

        return {"X": X.tolist(), "k": k}

    def solve(self, problem: dict[str, Any]) -> list[int]:
        try:
            # use sklearn.cluster.KMeans to solve the task
            kmeans = sklearn.cluster.KMeans(n_clusters=problem["k"]).fit(problem["X"])
            return kmeans.labels_.tolist()
        except Exception as e:
            logging.error(f"Error: {e}")
            n = len(problem["X"])
            return [0] * n  # return trivial answer

    def is_solution(self, problem: dict[str, Any], solution: list[int]) -> bool:
        try:
            tol = 1e-5
            # first check if the solution only uses at most k clusters
            for c in solution:
                if c < 0 or c >= problem["k"]:
                    return False

            # now compute the loss
            def kmeans_loss(X, labels):
                X = np.array(X)
                labels = np.array(labels)
                n_clusters = np.max(labels) + 1

                loss = 0.0
                for k in range(n_clusters):
                    cluster_points = X[labels == k]
                    if len(cluster_points) == 0:
                        continue  # skip empty clusters
                    center = np.mean(cluster_points, axis=0)
                    loss += np.sum((cluster_points - center) ** 2)

                return loss

            solver_solution = self.solve(problem)
            error_solver = kmeans_loss(problem["X"], solver_solution)

            error_sol = kmeans_loss(problem["X"], solution)

            if 0.95 * error_sol > error_solver + tol:
                return False
            else:
                return True

        except Exception as e:
            logging.error(f"Error when verifying solution: {e}")
            return False