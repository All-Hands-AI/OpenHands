# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # ruff: noqa: E741
    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, np.ndarray | float]:
        np.random.seed(random_seed)

        # Randomize parameters
        a = 0.08 * np.random.uniform(0.8, 1.2)  # Time scale separation parameter
        b = 0.8 * np.random.uniform(0.9, 1.1)  # Recovery parameter
        c = 0.7 * np.random.uniform(0.9, 1.1)  # Recovery parameter
        I = 0.5 * np.random.uniform(0.9, 1.1)  # External stimulus current

        # Initial conditions with randomization
        v_init = -1.0 * np.random.uniform(0.9, 1.1)  # Initial membrane potential
        w_init = -0.5 * np.random.uniform(0.9, 1.1)  # Initial recovery variable

        # Scale integration time with n
        t0 = 0.0
        t1 = 100.0 * n  # Increase simulation time with n

        # Initial state vector
        y0 = np.array([v_init, w_init])

        # Parameters dictionary
        params = {"a": a, "b": b, "c": c, "I": I}

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "params": params}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        # ruff: noqa: E741
        def fitzhugh_nagumo(t, y):
            v, w = y  # v = membrane potential, w = recovery variable

            a = params["a"]
            b = params["b"]
            c = params["c"]
            I = params["I"]

            # FitzHugh-Nagumo equations
            dv_dt = v - (v**3) / 3 - w + I
            dw_dt = a * (b * v - c * w)

            return np.array([dv_dt, dw_dt])

        # Set solver parameters
        rtol = 1e-8
        atol = 1e-8

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            fitzhugh_nagumo,
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