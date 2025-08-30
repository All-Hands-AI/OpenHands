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

        # Number of bodies: 3+n
        num_bodies = 2 + n

        # Initialize arrays
        masses = np.zeros(num_bodies)
        positions = np.zeros((num_bodies, 3))  # x,y,z for each body
        velocities = np.zeros((num_bodies, 3))  # vx,vy,vz for each body

        # Central star
        masses[0] = 1.0  # Central mass normalized to 1.0

        # Orbiting planets with smaller masses
        for i in range(1, num_bodies):
            # Mass: random between 0.0001 and 0.001 of central mass
            masses[i] = 0.001 * np.random.uniform(0.3, 1.0)

            # Initial position: randomly distributed around central mass
            radius = 1.0 + (i - 1) * 0.5  # Start at 1.0 and increase by 0.5 each time
            radius *= np.random.uniform(0.9, 1.1)  # Small randomization

            theta = np.random.uniform(0, 2 * np.pi)
            positions[i, 0] = radius * np.cos(theta)
            positions[i, 1] = radius * np.sin(theta)
            positions[i, 2] = 0.01 * np.random.uniform(-1, 1)  # Small z component

            # Initial velocity for circular orbit: v = sqrt(G*M/r) with G=1
            v_circular = np.sqrt(masses[0] / radius)
            velocities[i, 0] = -v_circular * np.sin(theta)
            velocities[i, 1] = v_circular * np.cos(theta)
            velocities[i, 2] = 0.001 * np.random.uniform(-1, 1)

            # Add small perturbation to make orbits slightly elliptical
            velocities[i] *= np.random.uniform(0.95, 1.05)

        # Adjust system to ensure center of mass at origin and zero net momentum
        total_mass = np.sum(masses)
        com_position = np.sum(positions * masses[:, np.newaxis], axis=0) / total_mass
        com_velocity = np.sum(velocities * masses[:, np.newaxis], axis=0) / total_mass

        # Shift positions and velocities
        positions -= com_position
        velocities -= com_velocity

        # Flatten arrays for initial state: [all positions, all velocities]
        y0 = np.concatenate([positions.flatten(), velocities.flatten()])

        # Fixed integration time (short to avoid chaos)
        t0 = 0.0
        t1 = 5.0  # About 1-2 orbits for the closest planet

        # Softening parameter to prevent numerical issues during close encounters
        softening = 1e-4

        return {
            "t0": t0,
            "t1": t1,
            "y0": y0.tolist(),
            "masses": masses.tolist(),
            "softening": softening,
            "num_bodies": num_bodies,
        }

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        masses = np.array(problem["masses"])
        softening = problem["softening"]
        num_bodies = problem["num_bodies"]

        def nbodyproblem(t, y):
            # Reshape state into positions and velocities
            # [all positions, all velocities] format
            positions = y[: num_bodies * 3].reshape(num_bodies, 3)
            velocities = y[num_bodies * 3 :].reshape(num_bodies, 3)

            # Position derivatives = velocities
            dp_dt = velocities.reshape(-1)

            # Compute accelerations
            accelerations = np.zeros_like(positions)

            # Calculate all pairwise accelerations
            for i in range(num_bodies):
                for j in range(num_bodies):
                    if i != j:  # Skip self-interactions
                        # Vector from body i to body j
                        r_ij = positions[j] - positions[i]

                        # Squared distance with softening
                        dist_squared = np.sum(r_ij**2) + softening**2

                        # Force factor: G*m_j/r_ij³ (G=1 in our units)
                        factor = masses[j] / (dist_squared * np.sqrt(dist_squared))

                        # Acceleration contribution from body j to body i
                        accelerations[i] += factor * r_ij

            # Velocity derivatives = accelerations
            dv_dt = accelerations.reshape(-1)

            # Combine derivatives
            derivatives = np.concatenate([dp_dt, dv_dt])

            return derivatives

        # Set solver parameters
        rtol = 1e-8
        atol = 1e-8

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            nbodyproblem,
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
        if not all(k in problem for k in ["masses", "y0", "t0", "t1", "softening", "num_bodies"]):
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