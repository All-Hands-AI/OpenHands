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

        # Epidemiological parameters with randomization
        # Beta: transmission rate (0.2-0.5 per day)
        beta = 0.35 * np.random.uniform(0.5, 1.5)

        # Sigma: progression rate from exposed to infectious (1/sigma = incubation period)
        sigma = 0.2 * np.random.uniform(0.5, 1.5)  # ~5 day average incubation

        # Gamma: recovery rate (1/gamma = infectious period)
        gamma = 0.1 * np.random.uniform(0.5, 1.5)  # ~10 day average infectious period

        # Omega: rate of immunity loss (1/omega = duration of immunity)
        omega = 0.002 * np.random.uniform(0.5, 1.5)  # ~500 day immunity

        # Initial conditions with randomization
        initial_exposed_percent = 0.01 * np.random.uniform(0.5, 1.5)
        initial_infectious_percent = 0.005 * np.random.uniform(0.5, 1.5)
        initial_recovered_percent = 0.1 * np.random.uniform(0.7, 1.3)

        initial_susceptible = (
            1.0 - initial_exposed_percent - initial_infectious_percent - initial_recovered_percent
        )

        # Scale integration time with n - this is the actual difficulty parameter
        t0 = 0.0
        t1 = 10.0 * n  # days

        # Initial state vector as fractions (sums to 1.0)
        y0 = np.array(
            [
                initial_susceptible,
                initial_exposed_percent,
                initial_infectious_percent,
                initial_recovered_percent,
            ]
        )

        # Parameters dictionary
        params = {"beta": beta, "sigma": sigma, "gamma": gamma, "omega": omega}

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "params": params}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        # SEIRS model function
        # ruff: noqa: E741
        def seirs(t, y):
            # Unpack state variables (these are fractions of total population)
            S, E, I, R = y

            # Unpack parameters
            beta = params["beta"]
            sigma = params["sigma"]
            gamma = params["gamma"]
            omega = params["omega"]

            # Simplified SEIRS model equations without births/deaths
            dSdt = -beta * S * I + omega * R
            dEdt = beta * S * I - sigma * E
            dIdt = sigma * E - gamma * I
            dRdt = gamma * I - omega * R

            return np.array([dSdt, dEdt, dIdt, dRdt])

        # Set solver parameters equivalent to diffrax settings
        rtol = 1e-10
        atol = 1e-10

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            seirs,
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

    def is_solution(self, problem: dict[str, Any], solution: dict[str, list[float]]) -> bool:
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

        # Check if the solution components sum to approximately 1 (conservation law)
        if not np.isclose(np.sum(proposed_array), 1.0, rtol=1e-5, atol=1e-8):
            logging.error(
                f"Solution components sum to {np.sum(proposed_array)}, not 1.0 (conservation violation)."
            )
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