# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp



MAX_STEPS = 100_000  # integration budget


class Task:
    """
    Stiff Van der Pol oscillator (μ = 2ⁿ, n ≥ 0).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, np.ndarray | float]:
        rng = np.random.default_rng(random_seed)
        y0 = [rng.random(), 0.0]  # random initial displacement, zero velocity
        t0, t1 = 0.0, 10.0
        mu = n
        return {"mu": mu, "y0": y0, "t0": t0, "t1": t1}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = float(problem["t0"]), float(problem["t1"])
        mu = float(problem["mu"])

        def vdp(t, y):
            x, v = y
            dx_dt = v
            dv_dt = mu * ((1 - x**2) * v - x)
            return np.array([dx_dt, dv_dt])

        # Set solver parameters for stiff system
        rtol = 1e-8
        atol = 1e-9

        method = "Radau"  # Alternatives: 'LSODA' or 'BDF'
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            vdp,
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
        required = {"mu", "y0", "t0", "t1"}
        if not required.issubset(problem):
            logging.error("Problem dictionary missing required keys.")
            return False

        proposed = solution
        if not proposed:
            logging.error("Empty solution returned.")
            return False

        try:
            y0_arr = np.asarray(problem["y0"], dtype=float)
            prop_arr = np.asarray(proposed, dtype=float)
        except Exception:
            logging.error("Could not convert arrays.")
            return False

        if prop_arr.shape != y0_arr.shape:
            logging.error(f"Shape mismatch: {prop_arr.shape} vs {y0_arr.shape}.")
            return False
        if not np.all(np.isfinite(prop_arr)):
            logging.error("Proposed solution contains non-finite values.")
            return False

        try:
            ref_solution = self.solve(problem)
            ref_arr = np.array(ref_solution)
        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False
        if ref_arr.shape != y0_arr.shape or not np.all(np.isfinite(ref_arr)):
            logging.error("Reference solver failed internally.")
            return False

        rtol, atol = 1e-5, 1e-8
        if not np.allclose(prop_arr, ref_arr, rtol=rtol, atol=atol):
            abs_err = np.max(np.abs(prop_arr - ref_arr))
            rel_err = np.max(np.abs((prop_arr - ref_arr) / (np.abs(ref_arr) + atol)))
            logging.error(
                f"Solution verification failed: max abs err={abs_err:.3g}, "
                f"max rel err={rel_err:.3g}"
            )
            return False
        return True