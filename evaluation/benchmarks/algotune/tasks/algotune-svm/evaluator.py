# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any, Dict

import cvxpy as cp
import numpy as np



class Task:
    """
    Solves the support vector machine problem via convex optimization.

        min   ½‖β‖₂² + C ∑ᵢ ξᵢ
      β,β₀,ξ
        s.t. ξᵢ ≥ 0,                                  ∀ i
             yᵢ (xᵢᵀ β + β₀) ≥ 1 − ξᵢ,                ∀ i

    where
        β      : weight vector (opt. variable)
        β₀     : intercept      (opt. variable)
        xᵢ ∈ ℝᵖ : input vectors
        yᵢ ∈ {−1, 1}
        C > 0  : regularisation strength
        n      : number of samples
    """

    # ---------------------------------------------------------------------
    # Data generation
    # ---------------------------------------------------------------------
    def generate_problem(
        self,
        n: int,
        random_seed: int = 1,
    ) -> Dict[str, Any]:
        """
        Generates a random SVM instance whose difficulty scales with `n`.

        Returns
        -------
        dict with keys
            X : list[list[float]]
            y : list[int]
            C : float
        """
        n = max(n, 10)
        rng = np.random.default_rng(random_seed)

        # Dimensionality grows with n but is capped for practicality
        p = min(max(2, n // 50), 100)

        # -----------------------------------------------------------------
        # Class sizes – never drop a sample when n is odd
        # -----------------------------------------------------------------
        n_neg = n // 2          # ⌊n / 2⌋ negatives
        n_pos = n - n_neg       # ⌈n / 2⌉ positives
        class_counts = {-1: n_neg, 1: n_pos}

        # Difficulty: smaller separation, higher variance, extra clusters
        base_separation = 4.0 - min(2.5, n / 200.0)  # 4.0 → 1.5 as n grows
        separation_factor = base_separation + rng.uniform(-0.5, 0.5)
        num_clusters = min(1 + n // 500, 5)

        X_all, y_all = [], []

        for class_label in (-1, 1):
            n_class = class_counts[class_label]
            n_per_cluster = n_class // num_clusters
            n_remaining = n_class - n_per_cluster * num_clusters

            for cluster_idx in range(num_clusters):
                # ---------- cluster centre ----------
                if cluster_idx == 0:
                    if class_label == -1:
                        center = rng.normal(0, 0.5, size=p)
                    else:
                        direction = rng.normal(size=p)
                        direction /= np.linalg.norm(direction)
                        center = separation_factor * direction + rng.normal(0, 0.2, size=p)
                else:
                    if class_label == -1 and len(X_all) > 0:
                        base_center = X_all[0].mean(axis=0)
                    elif class_label == 1 and len(X_all) > n_neg:
                        base_center = X_all[n_neg].mean(axis=0)
                    else:
                        base_center = np.zeros(p)
                    offset = rng.normal(0, separation_factor * 0.3, size=p)
                    center = base_center + offset

                # ---------- covariance ----------
                base_variance = 0.5 + min(1.5, n / 1000.0)  # 0.5 → 2.0
                cov = np.eye(p) * base_variance
                if n > 100 and p > 2:
                    Q, _ = np.linalg.qr(rng.normal(size=(p, p)))
                    eigenvalues = rng.uniform(0.5, 2.0, size=p) * base_variance
                    cov = Q @ np.diag(eigenvalues) @ Q.T

                # ---------- points ----------
                n_points = n_per_cluster + (n_remaining if cluster_idx == 0 else 0)
                X_cluster = rng.multivariate_normal(center, cov, size=n_points)
                X_all.append(X_cluster)
                y_all.extend([class_label] * n_points)

        X = np.vstack(X_all)
        y = np.array(y_all)
        n_samples = X.shape[0]  # == n by construction

        # -----------------------------------------------------------------
        # Outliers
        # -----------------------------------------------------------------
        outlier_fraction = min(0.1, n_samples / 5000.0)
        n_outliers = int(n_samples * outlier_fraction)
        if n_outliers:
            outlier_idx = rng.choice(n_samples, n_outliers, replace=False)
            for idx in outlier_idx:
                if rng.random() < 0.5:
                    y[idx] = -y[idx]                # label flip
                else:
                    X[idx] += rng.normal(0, separation_factor, size=p)  # move

        # Shuffle
        shuffle_idx = rng.permutation(n_samples)
        X, y = X[shuffle_idx], y[shuffle_idx]

        # -----------------------------------------------------------------
        # Regularisation parameter
        # -----------------------------------------------------------------
        C_base = 10.0 / (1.0 + n / 100.0)
        C = C_base * rng.uniform(0.5, 2.0)

        return {"X": X.tolist(), "y": y.tolist(), "C": C}

    # ---------------------------------------------------------------------
    # Solver
    # ---------------------------------------------------------------------
    def solve(
        self,
        problem: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Solves the SVM using CVXPY and returns
            beta0 : float
            beta  : list[float]
            optimal_value : float
            missclass_error : float
        """
        X = np.array(problem["X"])
        y = np.array(problem["y"])[:, None]
        C = float(problem["C"])

        p, n = X.shape[1], X.shape[0]

        beta = cp.Variable((p, 1))
        beta0 = cp.Variable()
        xi = cp.Variable((n, 1))

        objective = cp.Minimize(0.5 * cp.sum_squares(beta) + C * cp.sum(xi))
        constraints = [
            xi >= 0,
            cp.multiply(y, X @ beta + beta0) >= 1 - xi,
        ]

        prob = cp.Problem(objective, constraints)
        try:
            optimal_value = prob.solve()
        except cp.SolverError as e:
            logging.error(f"CVXPY Solver Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Error during solve: {e}")
            return None

        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            logging.warning(f"Solver status: {prob.status}")

        if beta.value is None or beta0.value is None:
            logging.warning("Solver finished without a solution.")
            return None

        pred = X @ beta.value + beta0.value
        missclass = np.mean((pred * y) < 0)

        return {
            "beta0": float(beta0.value),
            "beta": beta.value.flatten().tolist(),
            "optimal_value": float(optimal_value),
            "missclass_error": float(missclass),
        }

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    def is_solution(
        self,
        problem: Dict[str, Any],
        solution: Dict[str, Any],
    ) -> bool:
        """
        Verifies the supplied solution against a fresh solve() result.
        """
        reference = self.solve(problem)
        if reference is None:
            raise RuntimeError("Reference solver failed; cannot validate.")

        keys = ("beta0", "beta", "optimal_value", "missclass_error")
        if any(k not in solution for k in keys):
            logging.error("Solution missing required keys.")
            return False

        beta = np.array(solution["beta"], dtype=float)
        expected_beta = np.array(reference["beta"])

        p = np.array(problem["X"]).shape[1]
        if beta.shape != expected_beta.shape or beta.size != p:
            logging.error("Incorrect beta dimension.")
            return False

        if not np.allclose(beta, expected_beta, atol=1e-6):
            logging.error("Beta not optimal.")
            return False
        if not np.isclose(solution["beta0"], reference["beta0"], atol=1e-6):
            logging.error("Beta0 not optimal.")
            return False
        if not np.isclose(solution["optimal_value"], reference["optimal_value"], atol=1e-6):
            logging.error("Objective value incorrect.")
            return False
        if not np.isclose(solution["missclass_error"], reference["missclass_error"], atol=1e-6):
            logging.error("Misclassification error incorrect.")
            return False

        return True