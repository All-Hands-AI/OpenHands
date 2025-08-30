#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from numba import njit

@njit(inline="always")
def alpha_m(V):
    # L'Hôpital's rule at V = -40
    if V == -40.0:
        return 1.0
    return 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))

@njit(inline="always")
def beta_m(V):
    return 4.0 * np.exp(-(V + 65.0) / 18.0)

@njit(inline="always")
def alpha_h(V):
    return 0.07 * np.exp(-(V + 65.0) / 20.0)

@njit(inline="always")
def beta_h(V):
    return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))

@njit(inline="always")
def alpha_n(V):
    # L'Hôpital's rule at V = -55
    if V == -55.0:
        return 0.1
    return 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))

@njit(inline="always")
def beta_n(V):
    return 0.125 * np.exp(-(V + 65.0) / 80.0)

@njit
def _rk4_integrate(t0, t1, y, C_m, g_Na, g_K, g_L,
                   E_Na, E_K, E_L, I_app, steps):
    dt = (t1 - t0) / steps
    V, m, h, n = y[0], y[1], y[2], y[3]
    for _ in range(steps):
        # k1
        I_Na = g_Na * m**3 * h * (V - E_Na)
        I_K = g_K * n**4 * (V - E_K)
        I_L = g_L * (V - E_L)
        k1_V = (I_app - I_Na - I_K - I_L) / C_m
        k1_m = alpha_m(V) * (1.0 - m) - beta_m(V) * m
        k1_h = alpha_h(V) * (1.0 - h) - beta_h(V) * h
        k1_n = alpha_n(V) * (1.0 - n) - beta_n(V) * n

        # k2
        V2 = V + 0.5 * dt * k1_V
        m2 = m + 0.5 * dt * k1_m
        h2 = h + 0.5 * dt * k1_h
        n2 = n + 0.5 * dt * k1_n
        I_Na = g_Na * m2**3 * h2 * (V2 - E_Na)
        I_K = g_K * n2**4 * (V2 - E_K)
        I_L = g_L * (V2 - E_L)
        k2_V = (I_app - I_Na - I_K - I_L) / C_m
        k2_m = alpha_m(V2) * (1.0 - m2) - beta_m(V2) * m2
        k2_h = alpha_h(V2) * (1.0 - h2) - beta_h(V2) * h2
        k2_n = alpha_n(V2) * (1.0 - n2) - beta_n(V2) * n2

        # k3
        V3 = V + 0.5 * dt * k2_V
        m3 = m + 0.5 * dt * k2_m
        h3 = h + 0.5 * dt * k2_h
        n3 = n + 0.5 * dt * k2_n
        I_Na = g_Na * m3**3 * h3 * (V3 - E_Na)
        I_K = g_K * n3**4 * (V3 - E_K)
        I_L = g_L * (V3 - E_L)
        k3_V = (I_app - I_Na - I_K - I_L) / C_m
        k3_m = alpha_m(V3) * (1.0 - m3) - beta_m(V3) * m3
        k3_h = alpha_h(V3) * (1.0 - h3) - beta_h(V3) * h3
        k3_n = alpha_n(V3) * (1.0 - n3) - beta_n(V3) * n3

        # k4
        V4 = V + dt * k3_V
        m4 = m + dt * k3_m
        h4 = h + dt * k3_h
        n4 = n + dt * k3_n
        I_Na = g_Na * m4**3 * h4 * (V4 - E_Na)
        I_K = g_K * n4**4 * (V4 - E_K)
        I_L = g_L * (V4 - E_L)
        k4_V = (I_app - I_Na - I_K - I_L) / C_m
        k4_m = alpha_m(V4) * (1.0 - m4) - beta_m(V4) * m4
        k4_h = alpha_h(V4) * (1.0 - h4) - beta_h(V4) * h4
        k4_n = alpha_n(V4) * (1.0 - n4) - beta_n(V4) * n4

        # Update
        V += (dt / 6.0) * (k1_V + 2*k2_V + 2*k3_V + k4_V)
        m += (dt / 6.0) * (k1_m + 2*k2_m + 2*k3_m + k4_m)
        h += (dt / 6.0) * (k1_h + 2*k2_h + 2*k3_h + k4_h)
        n += (dt / 6.0) * (k1_n + 2*k2_n + 2*k3_n + k4_n)

        # Clip gating variables
        if m < 0.0: m = 0.0
        elif m > 1.0: m = 1.0
        if h < 0.0: h = 0.0
        elif h > 1.0: h = 1.0
        if n < 0.0: n = 0.0
        elif n > 1.0: n = 1.0

    y[0], y[1], y[2], y[3] = V, m, h, n

class Solver:
    def solve(self, problem, **kwargs):
        # Unpack problem
        t0 = problem["t0"]
        t1 = problem["t1"]
        y = np.array(problem["y0"], dtype=np.float64)
        p = problem["params"]
        # Simulation parameters
        dt = 0.0125
        steps = int(np.ceil((t1 - t0) / dt))
        # Call compiled integrator
        _rk4_integrate(t0, t1, y,
                       p["C_m"], p["g_Na"], p["g_K"], p["g_L"],
                       p["E_Na"], p["E_K"], p["E_L"], p["I_app"],
                       steps)
        return y.tolist()
EOF
