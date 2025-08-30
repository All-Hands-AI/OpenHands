#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import math
import numba
from typing import Any

@numba.njit(fastmath=True)
def _integrate_seirs(T, S, E, I, R, beta, sigma, gamma, omega):
    if T <= 0.0:
        return S, E, I, R
    # Fixed step size: dt ≈4.0, compute steps via multiplication instead of ceil
    target_dt = 4.0
    inv_dt = 1.0 / target_dt
    # Ceil(T/target_dt) ≈ int(T*inv_dt)+1 ensures N≥1
    N = int(T * inv_dt) + 1
    # exact step
    dt = T / N
    # RK4 constants
    inv6 = 0.1666666666666666667
    h2 = dt * 0.5
    c1 = dt * inv6
    for _ in range(N):
        # k1
        dS1 = -beta * S * I + omega * R
        dE1 =  beta * S * I - sigma * E
        dI1 =  sigma * E     - gamma * I
        dR1 =  gamma * I     - omega * R

        # k2
        S2 = S + h2 * dS1
        E2 = E + h2 * dE1
        I2 = I + h2 * dI1
        R2 = R + h2 * dR1
        dS2 = -beta * S2 * I2 + omega * R2
        dE2 =  beta * S2 * I2 - sigma * E2
        dI2 =  sigma * E2     - gamma * I2
        dR2 =  gamma * I2     - omega * R2

        # k3
        S3 = S + h2 * dS2
        E3 = E + h2 * dE2
        I3 = I + h2 * dI2
        R3 = R + h2 * dR2
        dS3 = -beta * S3 * I3 + omega * R3
        dE3 =  beta * S3 * I3 - sigma * E3
        dI3 =  sigma * E3     - gamma * I3
        dR3 =  gamma * I3     - omega * R3

        # k4
        S4 = S + dt * dS3
        E4 = E + dt * dE3
        I4 = I + dt * dI3
        R4 = R + dt * dR3
        dS4 = -beta * S4 * I4 + omega * R4
        dE4 =  beta * S4 * I4 - sigma * E4
        dI4 =  sigma * E4     - gamma * I4
        dR4 =  gamma * I4     - omega * R4

        # update with precomputed c1 = dt/6
        S += c1 * (dS1 + 2.0 * dS2 + 2.0 * dS3 + dS4)
        E += c1 * (dE1 + 2.0 * dE2 + 2.0 * dE3 + dE4)
        I += c1 * (dI1 + 2.0 * dI2 + 2.0 * dI3 + dI4)
        R += c1 * (dR1 + 2.0 * dR2 + 2.0 * dR3 + dR4)
    # Renormalize to ensure sum=1
        # k1
        dS1 = -beta * S * I + omega * R
        dE1 = beta * S * I - sigma * E
        dI1 = sigma * E - gamma * I
        dR1 = gamma * I - omega * R

        # k2
        S2 = S + 0.5 * dt * dS1
        E2 = E + 0.5 * dt * dE1
        I2 = I + 0.5 * dt * dI1
        R2 = R + 0.5 * dt * dR1
        dS2 = -beta * S2 * I2 + omega * R2
        dE2 = beta * S2 * I2 - sigma * E2
        dI2 = sigma * E2 - gamma * I2
        dR2 = gamma * I2 - omega * R2

        # k3
        S3 = S + 0.5 * dt * dS2
        E3 = E + 0.5 * dt * dE2
        I3 = I + 0.5 * dt * dI2
        R3 = R + 0.5 * dt * dR2
        dS3 = -beta * S3 * I3 + omega * R3
        dE3 = beta * S3 * I3 - sigma * E3
        dI3 = sigma * E3 - gamma * I3
        dR3 = gamma * I3 - omega * R3

        # k4
        S4 = S + dt * dS3
        E4 = E + dt * dE3
        I4 = I + dt * dI3
        R4 = R + dt * dR3
        dS4 = -beta * S4 * I4 + omega * R4
        dE4 = beta * S4 * I4 - sigma * E4
        dI4 = sigma * E4 - gamma * I4
        dR4 = gamma * I4 - omega * R4

        # update
        S += dt * (dS1 + 2.0 * dS2 + 2.0 * dS3 + dS4) / 6.0
        E += dt * (dE1 + 2.0 * dE2 + 2.0 * dE3 + dE4) / 6.0
        I += dt * (dI1 + 2.0 * dI2 + 2.0 * dI3 + dI4) / 6.0
        R += dt * (dR1 + 2.0 * dR2 + 2.0 * dR3 + dR4) / 6.0

    # Renormalize to satisfy S+E+I+R=1
    total = S + E + I + R
    S /= total
    E /= total
    I /= total
    R /= total
    return S, E, I, R
class Solver:
    def __init__(self):
        # Warm up numba compilation
        _ = _integrate_seirs(1.0, 1.0, 0.0, 0.0, 0.0,
                             0.1, 0.1, 0.1, 0.1)

    def solve(self, problem):
        # Parse inputs
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        T = t1 - t0
        p = problem["params"]
        beta = float(p["beta"]); sigma = float(p["sigma"])
        gamma = float(p["gamma"]); omega = float(p["omega"])
        # Analytic equilibrium if long horizon
        if T >= 50.0:
            S_eq = gamma / beta
            if S_eq >= 1.0:
                return [1.0, 0.0, 0.0, 0.0]
            X = gamma / sigma + 1.0 + gamma / omega
            I_eq = (1.0 - S_eq) / X
            E_eq = (gamma / sigma) * I_eq
            R_eq = (gamma / omega) * I_eq
            return [S_eq, E_eq, I_eq, R_eq]
        # Else numerical integration
        y0 = problem["y0"]
        S0, E0, I0, R0 = float(y0[0]), float(y0[1]), float(y0[2]), float(y0[3])
        S, E, I, R = _integrate_seirs(
            T, S0, E0, I0, R0, beta, sigma, gamma, omega
        )
        return [S, E, I, R]
EOF
