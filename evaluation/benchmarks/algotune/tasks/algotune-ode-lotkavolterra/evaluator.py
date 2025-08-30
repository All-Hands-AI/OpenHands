# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, np.ndarray | float]:
        np.random.seed(random_seed)

        # Randomize parameters within biologically plausible ranges
        alpha = 1.1 * np.random.uniform(0.8, 1.2)
        beta = 0.4 * np.random.uniform(0.8, 1.2)
        delta = 0.1 * np.random.uniform(0.8, 1.2)
        gamma = 0.4 * np.random.uniform(0.8, 1.2)

        # Initial conditions with randomization
        prey_init = 10.0 * np.random.uniform(0.8, 1.2)
        predator_init = 5.0 * np.random.uniform(0.8, 1.2)

        # Scale integration time with n
        t0 = 0.0
        t1 = 1.0 * n

        # Initial state vector
        y0 = np.array([prey_init, predator_init])

        # Parameters dictionary
        params = {"alpha": alpha, "beta": beta, "delta": delta, "gamma": gamma}

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "params": params}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        def lotka_volterra(t, y):
            # Unpack state variables
            x, y = y  # x = prey, y = predator

            # Unpack parameters
            alpha = params["alpha"]
            beta = params["beta"]
            delta = params["delta"]
            gamma = params["gamma"]

            # Lotka-Volterra equations
            dx_dt = alpha * x - beta * x * y
            dy_dt = delta * x * y - gamma * y

            return np.array([dx_dt, dy_dt])

        # Set solver parameters
        rtol = 1e-10
        atol = 1e-10

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            lotka_volterra,
            [t0, t1],
            y0,
            method=method,
            rtol=rtol,
            atol=atol,
            t_eval=t_eval,
            dense_output=debug,
        )

        if not sol.success:
            logging.warning(f"Solver failed: {sol.message}")

        return sol

    def solve(self, problem: dict[str, np.ndarray | float]) -> dict[str, list[float]]:
        sol = self._solve(problem, debug=False)

        # Extract final state
        if sol.success:
            return sol.y[:, -1].tolist()  # Get final state
        else:
            raise RuntimeError(f"Solver failed: {sol.message}")

    def is_solution(self, problem: dict[str, Any], solution: list[float]) -> bool:
        if not all(k in problem for k in ["params", "y0", "t0", "t1"]):
            logging.error("Problem dictionary missing required keys.")
            return False

        proposed_list = solution

        try:
            y0_arr = np.array(problem["y0"])
            proposed_array = np.array(proposed_list, dtype=float)
        except Exception:
            logging.error("Could not convert 'y_final' or 'y0' to numpy arrays.")
            return False

        if proposed_array.shape != y0_arr.shape:
            logging.error(f"Output shape {proposed_array.shape} != input shape {y0_arr.shape}.")
            return False
        if not np.all(np.isfinite(proposed_array)):
            logging.error("Proposed 'y_final' contains non-finite values.")
            return False
        if not np.all(proposed_array >= 0):
            logging.error("Proposed solution contains negative population values.")
            return False

        try:
            ref_solution = self.solve(problem)
            ref_array = np.array(ref_solution)
        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False

        if ref_array.shape != y0_arr.shape:
            logging.error(f"Reference shape {ref_array.shape} mismatch input {y0_arr.shape}.")
            return False
        if not np.all(np.isfinite(ref_array)):
            logging.error("Reference solution contains non-finite values.")
            return False

        rtol, atol = 1e-5, 1e-8
        if not np.allclose(proposed_array, ref_array, rtol=rtol, atol=atol):
            abs_diff = np.max(np.abs(proposed_array - ref_array))
            rel_diff = np.max(
                np.abs((proposed_array - ref_array) / (atol + rtol * np.abs(ref_array)))
            )
            logging.error(
                f"Solution verification failed: max abs err={abs_diff:.3g}, max rel err={rel_diff:.3g}"
            )
            return False

        return True