# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp



MAX_STEPS = 100_000


class Task:
    """
    Integrates the non-chaotic Lorenz-96 system (F = 2).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, np.ndarray | float]:
        rng = np.random.default_rng(random_seed)
        F = 2.0
        t0, t1 = 0.0, 10.0
        N = n + 4
        y0 = np.full(N, F) + rng.random(N) * 0.01
        return {"F": F, "t0": t0, "t1": t1, "y0": y0.tolist()}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = float(problem["t0"]), float(problem["t1"])
        F = float(problem["F"])

        def lorenz96(t, x):
            # Implement the Lorenz-96 model dynamics using numpy
            # x[i-1] (x[i+1] - x[i-2]) - x[i] + F
            N = len(x)
            dxdt = np.zeros_like(x)

            # Vectorized implementation
            ip1 = np.roll(np.arange(N), -1)  # i+1 indices
            im1 = np.roll(np.arange(N), 1)  # i-1 indices
            im2 = np.roll(np.arange(N), 2)  # i-2 indices

            dxdt = (x[ip1] - x[im2]) * x[im1] - x + F
            return dxdt

        # Set solver parameters
        rtol = 1e-8
        atol = 1e-8

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            lorenz96,
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
        if not {"F", "y0", "t0", "t1"}.issubset(problem):
            logging.error("Problem dict missing required keys.")
            return False

        proposed = solution
        if not proposed:
            logging.error("Empty solution returned.")
            return False

        try:
            y0_arr = np.asarray(problem["y0"], dtype=float)
            prop_arr = np.asarray(proposed, dtype=float)
        except Exception:
            logging.error("Could not convert to numpy arrays.")
            return False

        if prop_arr.shape != y0_arr.shape:
            logging.error(f"Shape mismatch: {prop_arr.shape} vs {y0_arr.shape}.")
            return False
        if not np.all(np.isfinite(prop_arr)):
            logging.error("Non-finite values detected in solution.")
            return False

        try:
            ref_solution = self.solve(problem)
            ref = np.array(ref_solution)
        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False
        if ref.shape != y0_arr.shape or not np.all(np.isfinite(ref)):
            logging.error("Reference solver failed internally.")
            return False

        if not np.allclose(prop_arr, ref, rtol=1e-5, atol=1e-8):
            abs_err = np.max(np.abs(prop_arr - ref))
            rel_err = np.max(np.abs((prop_arr - ref) / (np.abs(ref) + 1e-8)))
            logging.error(
                f"Verification failed: max abs err={abs_err:.3g}, max rel err={rel_err:.3g}"
            )
            return False

        return True