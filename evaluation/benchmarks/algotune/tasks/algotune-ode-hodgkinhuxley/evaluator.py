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

        # Membrane parameters with randomization
        C_m = 1.0 * np.random.uniform(0.9, 1.1)  # Membrane capacitance (μF/cm²)

        # Maximal conductances with slight randomization
        g_Na = 120.0 * np.random.uniform(0.9, 1.1)  # Sodium (Na) maximal conductance (mS/cm²)
        g_K = 36.0 * np.random.uniform(0.9, 1.1)  # Potassium (K) maximal conductance (mS/cm²)
        g_L = 0.3 * np.random.uniform(0.9, 1.1)  # Leak maximal conductance (mS/cm²)

        # Reversal potentials with slight randomization
        E_Na = 50.0 * np.random.uniform(0.95, 1.05)  # Sodium (Na) reversal potential (mV)
        E_K = -77.0 * np.random.uniform(0.95, 1.05)  # Potassium (K) reversal potential (mV)
        E_L = -54.4 * np.random.uniform(0.95, 1.05)  # Leak reversal potential (mV)

        # Applied stimulus current
        I_app = 10.0 * np.random.uniform(0.9, 1.1)  # Applied current (μA/cm²)

        # Initial conditions with randomization
        # Start with membrane at rest and channels at equilibrium
        V_init = -65.0 * np.random.uniform(0.98, 1.02)  # Initial membrane potential (mV)

        # Calculate steady-state values for gating variables at V_init
        alpha_n = (
            0.01 * (V_init + 55.0) / (1.0 - np.exp(-(V_init + 55.0) / 10.0))
            if V_init != -55.0
            else 0.1
        )
        beta_n = 0.125 * np.exp(-(V_init + 65.0) / 80.0)
        n_init = alpha_n / (alpha_n + beta_n)

        alpha_m = (
            0.1 * (V_init + 40.0) / (1.0 - np.exp(-(V_init + 40.0) / 10.0))
            if V_init != -40.0
            else 1.0
        )
        beta_m = 4.0 * np.exp(-(V_init + 65.0) / 18.0)
        m_init = alpha_m / (alpha_m + beta_m)

        alpha_h = 0.07 * np.exp(-(V_init + 65.0) / 20.0)
        beta_h = 1.0 / (1.0 + np.exp(-(V_init + 35.0) / 10.0))
        h_init = alpha_h / (alpha_h + beta_h)

        # Slight randomization of gating variables
        m_init = m_init * np.random.uniform(0.95, 1.05)
        h_init = h_init * np.random.uniform(0.95, 1.05)
        n_init = n_init * np.random.uniform(0.95, 1.05)

        # Ensure gating variables stay in [0, 1]
        m_init = max(0.0, min(1.0, m_init))
        h_init = max(0.0, min(1.0, h_init))
        n_init = max(0.0, min(1.0, n_init))

        # Scale integration time with n
        t0 = 0.0  # ms
        t1 = 1.0 * n  # ms

        # Initial state vector [V, m, h, n]
        y0 = np.array([V_init, m_init, h_init, n_init])

        # Parameters dictionary
        params = {
            "C_m": C_m,
            "g_Na": g_Na,
            "g_K": g_K,
            "g_L": g_L,
            "E_Na": E_Na,
            "E_K": E_K,
            "E_L": E_L,
            "I_app": I_app,
        }

        return {"t0": t0, "t1": t1, "y0": y0.tolist(), "params": params}

    def _solve(self, problem: dict[str, np.ndarray | float], debug=True) -> Any:
        y0 = np.array(problem["y0"])
        t0, t1 = problem["t0"], problem["t1"]
        params = problem["params"]

        def hodgkin_huxley(t, y):
            # Unpack state variables
            V, m, h, n = y  # V = membrane potential, m,h,n = gating variables

            # Unpack parameters
            C_m = params["C_m"]
            g_Na = params["g_Na"]
            g_K = params["g_K"]
            g_L = params["g_L"]
            E_Na = params["E_Na"]
            E_K = params["E_K"]
            E_L = params["E_L"]
            I_app = params["I_app"]

            # Calculate alpha and beta rate constants
            # Handle singularities in rate functions (when denominator approaches 0)
            if V == -40.0:
                alpha_m = 1.0  # L'Hôpital's rule limit at V = -40.0
            else:
                alpha_m = 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))

            beta_m = 4.0 * np.exp(-(V + 65.0) / 18.0)

            alpha_h = 0.07 * np.exp(-(V + 65.0) / 20.0)
            beta_h = 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))

            # Handle singularity in alpha_n at V = -55.0
            if V == -55.0:
                alpha_n = 0.1  # L'Hôpital's rule limit at V = -55.0
            else:
                alpha_n = 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))

            beta_n = 0.125 * np.exp(-(V + 65.0) / 80.0)

            # Ensure gating variables stay in [0, 1]
            m = np.clip(m, 0.0, 1.0)
            h = np.clip(h, 0.0, 1.0)
            n = np.clip(n, 0.0, 1.0)

            # Calculate ionic currents
            I_Na = g_Na * m**3 * h * (V - E_Na)
            I_K = g_K * n**4 * (V - E_K)
            I_L = g_L * (V - E_L)

            # Differential equations
            dVdt = (I_app - I_Na - I_K - I_L) / C_m
            dmdt = alpha_m * (1.0 - m) - beta_m * m
            dhdt = alpha_h * (1.0 - h) - beta_h * h
            dndt = alpha_n * (1.0 - n) - beta_n * n

            return np.array([dVdt, dmdt, dhdt, dndt])

        # Set solver parameters
        rtol = 1e-8
        atol = 1e-8

        method = "RK45"
        t_eval = np.linspace(t0, t1, 1000) if debug else None

        sol = solve_ivp(
            hodgkin_huxley,
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

        # Check if gating variables are in the valid range [0,1]
        if not (
            0 <= proposed_array[1] <= 1
            and 0 <= proposed_array[2] <= 1
            and 0 <= proposed_array[3] <= 1
        ):
            logging.error("Gating variables outside valid range [0,1].")
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