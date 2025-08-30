# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp



MAX_STEPS = 1_000_000  # integration budget


class Task:
    """
    Stiff Robertson chemical kinetics test problem.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, np.ndarray | float]:
        rng = np.random.default_rng(random_seed)
        k1 = 0.04 * rng.uniform(0.5, 2.0)
        k2 = 3e7 * rng.uniform(0.7, 1.5)
        k3 = 1e4 * rng.uniform(0.8, 1.3)
        t0, t1 = 0.0, 1.0 * n
        y0 = np.array([1.0, 0.0, 0.0])
        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "k": (k1, k2, k3)}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = float(problem["t0"]), float(problem["t1"])
        k = tuple(problem["k"])

        def rober(t, y):
            y1, y2, y3 = y
            k1, k2, k3 = k
            f0 = -k1 * y1 + k3 * y2 * y3
            f1 = k1 * y1 - k2 * y2**2 - k3 * y2 * y3
            f2 = k2 * y2**2
            return np.array([f0, f1, f2])

        # Set solver parameters for stiff system
        rtol = 1e-11
        atol = 1e-9

        method = "Radau"  # Alternatives: 'LSODA' or 'BDF'
        # Create logarithmically spaced time points for debugging
        if debug:
            t_eval = np.clip(np.exp(np.linspace(np.log(1e-6), np.log(t1), 1000)), t0, t1)
        else:
            t_eval = None

        sol = solve_ivp(
            rober,
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
        required = {"k", "y0", "t0", "t1"}
        if not required.issubset(problem):
            logging.error("Problem dictionary missing required keys.")
            return False

        proposed = solution

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
                f"Solution verification failed: max abs err={abs_err:.3g}, max rel err={rel_err:.3g}"
            )
            return False
        return True