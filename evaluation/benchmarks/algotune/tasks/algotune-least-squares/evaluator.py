# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.optimize import leastsq



def _safe_exp(z: np.ndarray | float) -> np.ndarray | float:
    """Exponentiation clipped to avoid overflow."""
    return np.exp(np.clip(z, -50.0, 50.0))


class Task:
    """
    Non-linear least-squares benchmark with several model families.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 42) -> dict[str, Any]:
        random.seed(random_seed)
        np.random.seed(random_seed)

        possible_models = ["polynomial", "exponential", "logarithmic", "sigmoid", "sinusoidal"]
        if n < 20:
            weights = [0.4, 0.2, 0.1, 0.1, 0.2]
        elif n < 100:
            weights = [0.3, 0.2, 0.15, 0.15, 0.2]
        else:
            weights = [0.2] * 5
        model_type = random.choices(possible_models, weights=weights, k=1)[0]

        degree = random.randint(1, min(8, max(1, n // 5))) if model_type == "polynomial" else None
        base_noise_factor = 0.05 + min(0.2, n / 500.0)
        noise_level = None
        x_range = (0.0, 1.0 + n / 10.0)
        param_range = (-5.0 - n / 50.0, 5.0 + n / 50.0)
        seasonality = random.random() < min(0.5, n / 150.0)
        outliers = random.random() < min(0.4, n / 100.0)
        outlier_fraction = random.uniform(0.03, 0.1)

        # ensure n ≥ number of parameters
        required_params = {
            "polynomial": (degree or 1) + 1,
            "exponential": 3,
            "logarithmic": 4,
            "sigmoid": 4,
            "sinusoidal": 4,
        }[model_type]
        if n < required_params:
            n = required_params

        x_data = (
            np.linspace(*x_range, n)
            if random.random() < 0.7
            else np.sort(np.random.uniform(*x_range, n))
        )

        problem: dict[str, Any] = {"n": n, "x_data": x_data.tolist(), "model_type": model_type}

        # --- model-specific ground-truth -------------------------------- #
        if model_type == "polynomial":
            true_params = np.random.uniform(*param_range, degree + 1)
            y_clean = np.polyval(true_params, x_data)
            problem["degree"] = degree

        elif model_type == "exponential":
            a = np.random.uniform(0.1, 3.0)
            b = np.random.uniform(0.01, 0.25)  # clip to keep exp argument small
            c = np.random.uniform(-3, 3)
            true_params = np.array([a, b, c])
            y_clean = a * _safe_exp(b * x_data) + c

        elif model_type == "logarithmic":
            x_data = np.maximum(x_data, 1e-3)
            a, b, c, d = np.random.uniform([0.5, 0.1, 0.1, -3], [5, 2, 2, 3])
            true_params = np.array([a, b, c, d])
            y_clean = a * np.log(b * x_data + c) + d

        elif model_type == "sigmoid":
            a = np.random.uniform(1, 5)
            b = np.random.uniform(0.2, 1.0)
            c = np.random.uniform(*x_range)
            d = np.random.uniform(-2, 2)
            true_params = np.array([a, b, c, d])
            y_clean = a / (1 + _safe_exp(-b * (x_data - c))) + d

        elif model_type == "sinusoidal":
            a = np.random.uniform(1, 5)
            b = np.random.uniform(0.1, 2)
            c = np.random.uniform(0, 2 * np.pi)
            d = np.random.uniform(-3, 3)
            true_params = np.array([a, b, c, d])
            y_clean = a * np.sin(b * x_data + c) + d

        if seasonality:
            a_s = np.random.uniform(0.2, 2)
            b_s = np.random.uniform(5, 20)
            y_clean += a_s * np.sin(b_s * x_data)

        if noise_level is None:
            y_std = max(1e-3, np.std(y_clean))  # avoid zero/NaN
            noise_level = max(0.01, base_noise_factor * y_std)
        noise = np.random.normal(0.0, noise_level, n)
        y_data = y_clean + noise

        if outliers:
            num_out = max(1, int(outlier_fraction * n))
            idx = random.sample(range(n), num_out)
            scale = np.random.uniform(3, 6)
            y_data[idx] += scale * noise_level * np.random.choice([-1, 1], size=num_out)

        problem["y_data"] = y_data.tolist()
        logging.debug("Generated least-squares instance (model=%s, n=%d)", model_type, n)
        return problem

    # ------------------------------------------------------------------ #
    # Residual function creator
    # ------------------------------------------------------------------ #
    def _create_residual_function(
        self, problem: dict[str, Any]
    ) -> tuple[Callable[[np.ndarray], np.ndarray], np.ndarray]:
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]

        if model_type == "polynomial":
            deg = problem["degree"]

            def r(p):
                return y_data - np.polyval(p, x_data)

            guess = np.ones(deg + 1)

        elif model_type == "exponential":

            def r(p):
                a, b, c = p
                return y_data - (a * _safe_exp(b * x_data) + c)

            guess = np.array([1.0, 0.05, 0.0])

        elif model_type == "logarithmic":

            def r(p):
                a, b, c, d = p
                return y_data - (a * np.log(b * x_data + c) + d)

            guess = np.array([1.0, 1.0, 1.0, 0.0])

        elif model_type == "sigmoid":

            def r(p):
                a, b, c, d = p
                return y_data - (a / (1 + _safe_exp(-b * (x_data - c))) + d)

            guess = np.array([3.0, 0.5, np.median(x_data), 0.0])

        elif model_type == "sinusoidal":

            def r(p):
                a, b, c, d = p
                return y_data - (a * np.sin(b * x_data + c) + d)

            guess = np.array([2.0, 1.0, 0.0, 0.0])

        else:
            raise ValueError(f"Unknown model type: {model_type}")

        return r, guess

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        residual, guess = self._create_residual_function(problem)
        params_opt, cov_x, info, mesg, ier = leastsq(
            residual, guess, full_output=True, maxfev=10000
        )

        # Calculate residuals and MSE
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]

        if model_type == "polynomial":
            y_fit = np.polyval(params_opt, x_data)
        elif model_type == "exponential":
            a, b, c = params_opt
            y_fit = a * _safe_exp(b * x_data) + c
        elif model_type == "logarithmic":
            a, b, c, d = params_opt
            y_fit = a * np.log(b * x_data + c) + d
        elif model_type == "sigmoid":
            a, b, c, d = params_opt
            y_fit = a / (1 + _safe_exp(-b * (x_data - c))) + d
        else:  # sinusoidal
            a, b, c, d = params_opt
            y_fit = a * np.sin(b * x_data + c) + d

        residuals = y_data - y_fit
        mse = float(np.mean(residuals**2))

        return {
            "params": params_opt.tolist(),
            "residuals": residuals.tolist(),
            "mse": mse,
            "convergence_info": {
                "success": ier in {1, 2, 3, 4},
                "status": int(ier),
                "message": mesg,
                "num_function_calls": int(info["nfev"]),
                "final_cost": float(np.sum(residuals**2)),
            },
        }

    def mse(self, problem: dict[str, Any], solution: dict[str, Any]) -> float:
        """Compute mean squared error for the given solution."""
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        params = np.asarray(solution["params"], dtype=float)
        model_type = problem["model_type"]

        if model_type == "polynomial":
            y_fit = np.polyval(params, x_data)
        elif model_type == "exponential":
            a, b, c = params
            y_fit = a * _safe_exp(b * x_data) + c
        elif model_type == "logarithmic":
            a, b, c, d = params
            y_fit = a * np.log(b * x_data + c) + d
        elif model_type == "sigmoid":
            a, b, c, d = params
            y_fit = a / (1 + _safe_exp(-b * (x_data - c))) + d
        else:  # sinusoidal
            a, b, c, d = params
            y_fit = a * np.sin(b * x_data + c) + d

        residuals = y_data - y_fit
        return float(np.mean(residuals**2))

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        mse = self.mse(problem, solution)

        reference_solution = self.solve(problem)
        ref_mse = self.mse(problem, reference_solution)

        return mse <= 1.05 * ref_mse