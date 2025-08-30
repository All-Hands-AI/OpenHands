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

        # Domain parameters
        x_min = 0.0
        x_max = 1.0

        # Diffusion coefficient with slight randomization
        alpha = 0.01 * np.random.uniform(0.8, 1.2)

        # Scale grid resolution with n
        base_points = 20  # Base number of interior points
        num_points = base_points * n  # Scale number of grid points with n

        # Create spatial grid (include boundary points)
        dx = (x_max - x_min) / (num_points + 1)
        x_grid = np.linspace(x_min + dx, x_max - dx, num_points)

        # Generate initial condition: combination of localized bumps with randomization
        # Bumps will be positioned away from boundaries to naturally satisfy boundary conditions
        u_init = np.zeros(num_points)
        num_bumps = np.random.randint(2, 5)  # Use 2-3 bumps

        for k in range(num_bumps):
            # Randomly position bump away from boundaries
            center = np.random.uniform(0.2, 0.8)  # Keep away from boundaries
            width = np.random.uniform(0.05, 0.15)  # Width of the bump
            sign = np.random.choice([-1, 1])  # Random sign
            amplitude = sign * np.random.uniform(0.8, 1.0)  # Height of the bump

            # Create smooth bump (compact support function)
            distance = np.abs(x_grid - center)
            u_init += amplitude * np.exp(-((distance / width) ** 2))

        # Normalize to keep amplitude reasonable
        if np.max(np.abs(u_init)) > 0:
            u_init = u_init / np.max(np.abs(u_init))

        # Scale integration time with n
        t0 = 0.0
        t1 = 2.0

        # Initial state vector
        y0 = np.array(u_init)

        # Parameters dictionary
        params = {"alpha": alpha, "dx": dx, "num_points": num_points}

        return {
            "t0": t0,
            "t1": t1,
            "y0": y0.tolist(),
            "params": params,
            "x_grid": x_grid.tolist(),  # Include grid for reference
        }

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        def heat_equation(t, u):
            # Extract parameters
            alpha = params["alpha"]
            dx = params["dx"]

            # Apply method of lines: discretize spatial derivatives using finite differences
            # For interior points, we use the standard central difference formula

            # Use padding to handle boundary conditions (u=0 at boundaries)
            u_padded = np.pad(u, 1, mode="constant", constant_values=0)

            # Compute second derivative using central difference
            u_xx = (u_padded[2:] - 2 * u_padded[1:-1] + u_padded[:-2]) / (dx**2)

            # Apply diffusion equation
            du_dt = alpha * u_xx

            return du_dt

        # Set solver parameters
        rtol = 1e-6
        atol = 1e-6

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            heat_equation,
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
            return sol.y[:, -1].tolist()
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