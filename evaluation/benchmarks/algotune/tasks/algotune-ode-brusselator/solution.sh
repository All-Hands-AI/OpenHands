#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import math
import numpy as np

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:  # pragma: no cover
    NUMBA_AVAILABLE = False

    def njit(*args, **kwargs):  # type: ignore
        def wrapper(func):
            return func
        return wrapper

@njit(fastmath=True, cache=True)
def _integrate_brusselator_numba(x0: float, y0: float, t0: float, t1: float,
                                 A: float, B: float, rtol: float, atol: float) -> Tuple[float, float]:
    # Precompute constants
    Bp1 = B + 1.0

    x = x0
    y = y0
    t = t0

    # Initial derivative
    x2 = x * x
    xy2 = x2 * y
    fx0 = A + xy2 - Bp1 * x
    fy0 = B * x - xy2

    # Initial step heuristic
    sx0 = atol + rtol * (x if x >= 0.0 else -x)
    sy0 = atol + rtol * (y if y >= 0.0 else -y)
    inv_sqrt2 = 0.7071067811865476
    d0 = math.hypot(x / sx0, y / sy0) * inv_sqrt2
    d1 = math.hypot(fx0 / sx0, fy0 / sy0) * inv_sqrt2
    if d0 < 1e-5 or d1 <= 1e-16:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1

    total = t1 - t0
    if h < 1e-12:
        h = 1e-12
    if h > total if total > 0.0 else h < total:
        h = total
    direction = 1.0 if total > 0.0 else -1.0
    h = h if total > 0.0 else -h

    # DP(5) coefficients
    a21 = 1.0 / 5.0

    a31 = 3.0 / 40.0
    a32 = 9.0 / 40.0

    a41 = 44.0 / 45.0
    a42 = -56.0 / 15.0
    a43 = 32.0 / 9.0

    a51 = 19372.0 / 6561.0
    a52 = -25360.0 / 2187.0
    a53 = 64448.0 / 6561.0
    a54 = -212.0 / 729.0

    a61 = 9017.0 / 3168.0
    a62 = -355.0 / 33.0
    a63 = 46732.0 / 5247.0
    a64 = 49.0 / 176.0
    a65 = -5103.0 / 18656.0

    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    bh1 = 5179.0 / 57600.0
    bh3 = 7571.0 / 16695.0
    bh4 = 393.0 / 640.0
    bh5 = -92097.0 / 339200.0
    bh6 = 187.0 / 2100.0
    bh7 = 1.0 / 40.0

    safety = 0.9
    min_factor = 0.2
    max_factor = 10.0
    inv_order = 0.2  # 1/5
    max_steps = 10000000

    steps = 0
    while True:
        steps += 1
        if steps > max_steps:
            break

        # Cap step to not overshoot t1
        dt = t1 - t
        if dt == 0.0:
            break
        if (dt > 0.0 and h > dt) or (dt < 0.0 and h < dt):
            h = dt

        # k1
        k1x = fx0
        k1y = fy0

        # k2
        x2 = x + h * a21 * k1x
        y2 = y + h * a21 * k1y
        x2x2 = x2 * x2
        xy2 = x2x2 * y2
        k2x = A + xy2 - Bp1 * x2
        k2y = B * x2 - xy2

        # k3
        x3 = x + h * (a31 * k1x + a32 * k2x)
        y3 = y + h * (a31 * k1y + a32 * k2y)
        x3x3 = x3 * x3
        xy3 = x3x3 * y3
        k3x = A + xy3 - Bp1 * x3
        k3y = B * x3 - xy3

        # k4
        x4 = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
        y4 = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
        x4x4 = x4 * x4
        xy4 = x4x4 * y4
        k4x = A + xy4 - Bp1 * x4
        k4y = B * x4 - xy4

        # k5
        x5 = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
        y5 = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
        x5x5 = x5 * x5
        xy5 = x5x5 * y5
        k5x = A + xy5 - Bp1 * x5
        k5y = B * x5 - xy5

        # k6
        x6 = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
        y6 = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
        x6x6 = x6 * x6
        xy6 = x6x6 * y6
        k6x = A + xy6 - Bp1 * x6
        k6y = B * x6 - xy6

        # 5th order solution
        y5x = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
        y5y = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

        # k7 at (t+h, y5)
        y5x2 = y5x * y5x
        xy7 = y5x2 * y5y
        k7x = A + xy7 - Bp1 * y5x
        k7y = B * y5x - xy7

        # 4th order solution using b_hat
        y4x = x + h * (bh1 * k1x + bh3 * k3x + bh4 * k4x + bh5 * k5x + bh6 * k6x + bh7 * k7x)
        y4y = y + h * (bh1 * k1y + bh3 * k3y + bh4 * k4y + bh5 * k5y + bh6 * k6y + bh7 * k7y)

        # Error estimate and norm
        ex = y5x - y4x
        ey = y5y - y4y
        ax = x if x >= 0.0 else -x
        ay = y if y >= 0.0 else -y
        a5x = y5x if y5x >= 0.0 else -y5x
        a5y = y5y if y5y >= 0.0 else -y5y
        sx = atol + rtol * (ax if ax >= a5x else a5x)
        sy = atol + rtol * (ay if ay >= a5y else a5y)
        dx = ex / sx
        dy = ey / sy
        err = math.hypot(dx, dy) * inv_sqrt2

        if err <= 1.0:
            # Accept step
            t += h
            x = y5x
            y = y5y
            # FSAL
            fx0 = k7x
            fy0 = k7y

            if t == t1:
                break

            # Step size update
            if err == 0.0:
                factor = max_factor
            else:
                factor = safety * (err ** (-inv_order))
                if factor < min_factor:
                    factor = min_factor
                elif factor > max_factor:
                    factor = max_factor
            h *= factor
        else:
            # Reject step
            factor = safety * (err ** (-inv_order))
            if factor < min_factor:
                factor = min_factor
            h *= factor

    return x, y

def _integrate_brusselator_py(x0: float, y0: float, t0: float, t1: float,
                              A: float, B: float, rtol: float, atol: float) -> Tuple[float, float]:
    # Fallback Python implementation (same as numba kernel)
    Bp1 = B + 1.0

    x = x0
    y = y0
    t = t0

    x2 = x * x
    xy2 = x2 * y
    fx0 = A + xy2 - Bp1 * x
    fy0 = B * x - xy2

    sx0 = atol + rtol * abs(x)
    sy0 = atol + rtol * abs(y)
    inv_sqrt2 = 0.7071067811865476
    d0 = math.hypot(x / sx0, y / sy0) * inv_sqrt2
    d1 = math.hypot(fx0 / sx0, fy0 / sy0) * inv_sqrt2
    if d0 < 1e-5 or d1 <= 1e-16:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1

    total = t1 - t0
    if h < 1e-12:
        h = 1e-12
    if (total > 0.0 and h > total) or (total < 0.0 and h < total):
        h = total
    direction = 1.0 if total > 0.0 else -1.0
    h = h if total > 0.0 else -h

    a21 = 1.0 / 5.0

    a31 = 3.0 / 40.0
    a32 = 9.0 / 40.0

    a41 = 44.0 / 45.0
    a42 = -56.0 / 15.0
    a43 = 32.0 / 9.0

    a51 = 19372.0 / 6561.0
    a52 = -25360.0 / 2187.0
    a53 = 64448.0 / 6561.0
    a54 = -212.0 / 729.0

    a61 = 9017.0 / 3168.0
    a62 = -355.0 / 33.0
    a63 = 46732.0 / 5247.0
    a64 = 49.0 / 176.0
    a65 = -5103.0 / 18656.0

    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    bh1 = 5179.0 / 57600.0
    bh3 = 7571.0 / 16695.0
    bh4 = 393.0 / 640.0
    bh5 = -92097.0 / 339200.0
    bh6 = 187.0 / 2100.0
    bh7 = 1.0 / 40.0

    safety = 0.9
    min_factor = 0.2
    max_factor = 10.0
    inv_order = 0.2
    max_steps = 10000000

    steps = 0
    while True:
        steps += 1
        if steps > max_steps:
            break

        dt = t1 - t
        if dt == 0.0:
            break
        if (dt > 0.0 and h > dt) or (dt < 0.0 and h < dt):
            h = dt

        k1x = fx0
        k1y = fy0

        x2 = x + h * a21 * k1x
        y2 = y + h * a21 * k1y
        x2x2 = x2 * x2
        xy2 = x2x2 * y2
        k2x = A + xy2 - Bp1 * x2
        k2y = B * x2 - xy2

        x3 = x + h * (a31 * k1x + a32 * k2x)
        y3 = y + h * (a31 * k1y + a32 * k2y)
        x3x3 = x3 * x3
        xy3 = x3x3 * y3
        k3x = A + xy3 - Bp1 * x3
        k3y = B * x3 - xy3

        x4 = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
        y4 = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
        x4x4 = x4 * x4
        xy4 = x4x4 * y4
        k4x = A + xy4 - Bp1 * x4
        k4y = B * x4 - xy4

        x5 = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
        y5 = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
        x5x5 = x5 * x5
        xy5 = x5x5 * y5
        k5x = A + xy5 - Bp1 * x5
        k5y = B * x5 - xy5

        x6 = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
        y6 = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
        x6x6 = x6 * x6
        xy6 = x6x6 * y6
        k6x = A + xy6 - Bp1 * x6
        k6y = B * x6 - xy6

        y5x = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
        y5y = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

        y5x2 = y5x * y5x
        xy7 = y5x2 * y5y
        k7x = A + xy7 - Bp1 * y5x
        k7y = B * y5x - xy7

        y4x = x + h * (bh1 * k1x + bh3 * k3x + bh4 * k4x + bh5 * k5x + bh6 * k6x + bh7 * k7x)
        y4y = y + h * (bh1 * k1y + bh3 * k3y + bh4 * k4y + bh5 * k5y + bh6 * k6y + bh7 * k7y)

        ex = y5x - y4x
        ey = y5y - y4y
        sx = atol + rtol * max(abs(x), abs(y5x))
        sy = atol + rtol * max(abs(y), abs(y5y))
        dx = ex / sx
        dy = ey / sy
        err = math.hypot(dx, dy) * inv_sqrt2

        if err <= 1.0:
            t += h
            x = y5x
            y = y5y
            fx0 = k7x
            fy0 = k7y

            if t == t1:
                break

            if err == 0.0:
                factor = max_factor
            else:
                factor = safety * (err ** (-inv_order))
                if factor < min_factor:
                    factor = min_factor
                elif factor > max_factor:
                    factor = max_factor
            h *= factor
        else:
            factor = safety * (err ** (-inv_order))
            if factor < min_factor:
                factor = min_factor
            h *= factor

    return x, y

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Any:
        # Extract problem data
        y0_list: List[float] = problem["y0"]
        t0: float = float(problem["t0"])
        t1: float = float(problem["t1"])
        params: Dict[str, float] = problem["params"]
        A: float = float(params["A"])
        B: float = float(params["B"])

        # Convert initial conditions
        x0 = float(y0_list[0])
        y0 = float(y0_list[1])

        # If no integration needed
        if t1 == t0:
            return np.array([x0, y0], dtype=float)

        # Integration settings (tighter than checker tolerance for safety)
        rtol = 1e-8
        atol = 1e-8

        if NUMBA_AVAILABLE:
            x, y = _integrate_brusselator_numba(x0, y0, t0, t1, A, B, rtol, atol)
        else:
            x, y = _integrate_brusselator_py(x0, y0, t0, t1, A, B, rtol, atol)

        return np.array([x, y], dtype=float)
EOF
