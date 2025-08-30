#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict
import numba
import math

@numba.njit(fastmath=True, cache=True)
def _rk4(mu: float, x0: float, v0: float, t0: float, t1: float):
    duration = t1 - t0
    # stability-limited dt (explicit RK4 stability ~2.78/mu)
    dt0 = 2.78 / mu
    # error-limited dt for tol=1e-8: dt^4 ~ tol/duration
    dt_error = math.sqrt(math.sqrt(1e-8 / duration))
    dt = dt0 if dt0 < dt_error else dt_error
    # number of steps
    N = int(duration / dt) + 1
    dt = duration / N
    half_dt = 0.5 * dt
    inv6_dt = dt / 6.0
    x = x0
    v = v0
    for _ in range(N):
        k1x = v
        k1v = mu * ((1.0 - x * x) * v - x)
        xt = x + half_dt * k1x
        vt = v + half_dt * k1v
        k2x = vt
        k2v = mu * ((1.0 - xt * xt) * vt - xt)
        xt = x + half_dt * k2x
        vt = v + half_dt * k2v
        k3x = vt
        k3v = mu * ((1.0 - xt * xt) * vt - xt)
        xt = x + dt * k3x
        vt = v + dt * k3v
        k4x = vt
        k4v = mu * ((1.0 - xt * xt) * vt - xt)
        x += inv6_dt * (k1x + 2.0 * k2x + 2.0 * k3x + k4x)
        v += inv6_dt * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return x, v

class Solver:
    def __init__(self):
        # Warm up Numba compilation
        _rk4(1.0, 0.0, 0.0, 0.0, 1.0)

    def solve(self, problem: Dict[str, Any], **kwargs) -> Any:
        mu = float(problem["mu"])
        y0 = problem["y0"]
        x0 = float(y0[0])
        v0 = float(y0[1])
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        x_final, v_final = _rk4(mu, x0, v0, t0, t1)
        return [x_final, v_final]
EOF
