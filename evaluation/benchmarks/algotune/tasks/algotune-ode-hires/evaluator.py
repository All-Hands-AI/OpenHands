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

        # Rate constants for HIRES with ±20% randomization
        c1 = 1.71 * np.random.uniform(0.9, 1.1)
        c2 = 0.43 * np.random.uniform(0.9, 1.1)
        c3 = 8.32 * np.random.uniform(0.9, 1.1)
        c4 = 0.0007 * np.random.uniform(0.9, 1.1)
        c5 = 8.75 * np.random.uniform(0.9, 1.1)
        c6 = 10.03 * np.random.uniform(0.9, 1.1)
        c7 = 0.035 * np.random.uniform(0.9, 1.1)
        c8 = 1.12 * np.random.uniform(0.9, 1.1)
        c9 = 1.745 * np.random.uniform(0.9, 1.1)
        c10 = 280.0 * np.random.uniform(0.9, 1.1)
        c11 = 0.69 * np.random.uniform(0.9, 1.1)
        c12 = 1.81 * np.random.uniform(0.9, 1.1)

        constants = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12]

        # Scale time span with n
        t0 = 0.0
        t1 = 1.0 * n

        # Initial conditions with slight randomization for the last component
        y8_init = 0.0057 * np.random.uniform(0.9, 1.1)
        y0 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, y8_init])

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "constants": constants}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        constants = problem["constants"]

        # Define the HIRES ODE system function
        def hires(t, y):
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12 = constants
            y1, y2, y3, y4, y5, y6, y7, y8 = y

            # HIRES system of equations
            f1 = -c1 * y1 + c2 * y2 + c3 * y3 + c4
            f2 = c1 * y1 - c5 * y2
            f3 = -c6 * y3 + c2 * y4 + c7 * y5
            f4 = c3 * y2 + c1 * y3 - c8 * y4
            f5 = -c9 * y5 + c2 * y6 + c2 * y7
            f6 = -c10 * y6 * y8 + c11 * y4 + c1 * y5 - c2 * y6 + c11 * y7
            f7 = c10 * y6 * y8 - c12 * y7
            f8 = -c10 * y6 * y8 + c12 * y7

            return np.array([f1, f2, f3, f4, f5, f6, f7, f8])

        # Set solver parameters equivalent to diffrax settings
        rtol = 1e-10
        atol = 1e-9

        method = "Radau"  # Alternatives: 'LSODA', 'BDF'
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        # Adding max_step to avoid excessive internal step size
        sol = solve_ivp(
            hires,
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
        if not all(k in problem for k in ["constants", "y0", "t0", "t1"]):
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