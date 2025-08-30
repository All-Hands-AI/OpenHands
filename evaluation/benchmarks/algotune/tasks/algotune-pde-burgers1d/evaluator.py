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
        x_min = -1.0
        x_max = 1.0

        # Fixed low viscosity to ensure shock formation
        # Low enough to create shocks but not so low that numerical issues occur
        nu = 0.005

        # Scale only grid resolution with n
        base_points = 20  # Base number of interior points
        num_points = base_points * n  # Scale number of grid points with n

        # Create spatial grid (include boundary points)
        dx = (x_max - x_min) / (num_points + 1)
        x_grid = np.linspace(x_min + dx, x_max - dx, num_points)

        # Generate initial condition designed to produce shocks
        # Use a combination of sine wave and step function
        u_init = np.zeros(num_points)

        # Choose one of several initial conditions that reliably produce shocks
        condition_type = np.random.randint(0, 3)

        if condition_type == 0:
            # Condition 1: Sine wave (creates shock in the middle)
            u_init = 0.5 * np.sin(np.pi * x_grid)

        elif condition_type == 1:
            # Condition 2: Positive bump (creates shock on right side)
            center = np.random.uniform(-0.5, -0.2)
            width = 0.3
            u_init = np.exp(-((x_grid - center) ** 2) / (2 * width**2))

        else:
            # Condition 3: Two oppositely signed bumps (creates shock between them)
            center1 = -0.5
            center2 = 0.5
            width = 0.2
            u_init = np.exp(-((x_grid - center1) ** 2) / (2 * width**2)) - 0.7 * np.exp(
                -((x_grid - center2) ** 2) / (2 * width**2)
            )

        # Apply small random perturbation for diversity
        u_init += 0.05 * np.random.uniform(-1, 1, size=num_points)

        # Fixed time for simulation
        t0 = 0.0
        t1 = 5.0  # Fixed time horizon

        # Initial state vector
        y0 = np.array(u_init)

        # Parameters dictionary
        params = {"nu": nu, "dx": dx, "num_points": num_points}

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

        def burgers_equation(t, u):
            # Extract parameters
            nu = params["nu"]
            dx = params["dx"]

            # Apply method of lines: discretize spatial derivatives
            # Pad array for boundary conditions (u=0 at boundaries)
            u_padded = np.pad(u, 1, mode="constant", constant_values=0)

            # For Burgers' equation, we need to discretize:
            # du/dt + u * du/dx = nu * d²u/dx²

            # First compute diffusion term (second derivative) using central difference
            diffusion_term = (u_padded[2:] - 2 * u_padded[1:-1] + u_padded[:-2]) / (dx**2)

            # For the advection term (u * du/dx), use an upwind scheme for stability
            # Implementation of a simple upwind scheme based on sign of u:
            u_centered = u_padded[1:-1]  # u at current point

            # Forward difference (for u < 0)
            du_dx_forward = (u_padded[2:] - u_padded[1:-1]) / dx

            # Backward difference (for u > 0)
            du_dx_backward = (u_padded[1:-1] - u_padded[:-2]) / dx

            # Choose appropriate differencing based on sign of u (upwind scheme)
            advection_term = np.where(
                u_centered >= 0,
                u_centered * du_dx_backward,  # Use backward difference when u ≥ 0
                u_centered * du_dx_forward,  # Use forward difference when u < 0
            )

            # Combine terms: du/dt = -u*du/dx + nu*d²u/dx²
            du_dt = -advection_term + nu * diffusion_term

            return du_dt

        # Set solver parameters
        rtol = 1e-6
        atol = 1e-6

        method = "RK45"
        t_eval = np.linspace(t0, t1, 100) if debug else None

        sol = solve_ivp(
            burgers_equation,
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