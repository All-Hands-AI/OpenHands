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

        # Brusselator parameters with randomization
        # Ensure oscillatory regime by keeping B > 1 + A²
        A = 1.0 * np.random.uniform(0.9, 1.1)
        # Choose B to ensure oscillations (B > 1 + A²)
        B_min = 1.0 + A**2 + 0.5  # Add margin to ensure we're in oscillatory regime
        B = B_min * np.random.uniform(1.0, 1.2)

        # Initial conditions with randomization
        # Start near but not exactly at the fixed point (A, B/A)
        x_init = A * np.random.uniform(0.8, 1.2)
        y_init = (B / A) * np.random.uniform(0.8, 1.2)

        # Scale integration time with n
        t0 = 0.0
        t1 = 1.0 * n  # Increase simulation time with n

        # Initial state vector
        y0 = np.array([x_init, y_init])

        # Parameters dictionary
        params = {"A": A, "B": B}

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "params": params}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        def brusselator(t, y):
            X, Y = y  # X and Y are concentrations of chemical species

            A = params["A"]
            B = params["B"]

            # Brusselator equations
            dX_dt = A + X**2 * Y - (B + 1) * X
            dY_dt = B * X - X**2 * Y

            return np.array([dX_dt, dY_dt])

        # Set solver parameters equivalent to diffrax settings
        rtol = 1e-8
        atol = 1e-8

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            brusselator,
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
            return sol.y[:, -1]  # Get final state
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