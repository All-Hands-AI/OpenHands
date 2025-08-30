#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict, List

try:
    from numba import njit  # type: ignore
except Exception:

    def njit(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

@njit(cache=True, fastmath=True)
def _integrate_dp45(
    t0: float,
    t1: float,
    v0: float,
    w0: float,
    a: float,
    b: float,
    c: float,
    I: float,
    rtol: float,
    atol: float,
) -> tuple:
    # Dormand–Prince RK45 coefficients used (a21..a65, b, b*)
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

    # 5th order solution weights (b)
    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    # Error weights e = b - bs for embedded 4th order estimate
    e1 = 71.0 / 57600.0
    e3 = -71.0 / 16695.0
    e4 = 71.0 / 1920.0
    e5 = -17253.0 / 339200.0
    e6 = 22.0 / 525.0
    e7 = -1.0 / 40.0

    # Precompute constants for RHS
    inv3 = 1.0 / 3.0
    ab = a * b
    ac = a * c

    t = t0
    v = float(v0)
    w = float(w0)
    direction = 1.0 if t1 >= t0 else -1.0
    t_end = t1

    # Initial derivative k1 = f(v, w)
    v2 = v * v
    v3 = v2 * v
    k1v = v - inv3 * v3 - w + I
    k1w = ab * v - ac * w

    # Initial step size heuristic
    sv0 = atol + rtol * (v if v >= 0.0 else -v)
    sw0 = atol + rtol * (w if w >= 0.0 else -w)
    d0 = ((v / sv0) ** 2 + (w / sw0) ** 2) ** 0.5
    d1 = ((k1v / sv0) ** 2 + (k1w / sw0) ** 2) ** 0.5
    if d0 < 1e-5 or d1 < 1e-5:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1
    rem = t_end - t
    if rem < 0.0:
        rem = -rem
    if h * direction > 0.0:
        h = (rem if rem < h else h) * direction
    else:
        h = (rem if rem < (h if h >= 0.0 else -h) else (h if h >= 0.0 else -h)) * direction

    SAFETY = 0.9
    MIN_FACTOR = 0.2
    MAX_FACTOR = 20.0
    ORDER = 5.0
    INV_SQRT2 = 0.7071067811865476

    # Integrate until reaching t1
    while (t - t_end) * direction + 1e-18 < 0.0:
        # Ensure we don't step past the end
        if (t + h - t_end) * direction > 0.0:
            h = t_end - t

        # Stage 2
        y2v = v + h * (a21 * k1v)
        y2w = w + h * (a21 * k1w)
        z = y2v
        z2 = z * z
        z3 = z2 * z
        k2v = z - inv3 * z3 - y2w + I
        k2w = ab * y2v - ac * y2w

        # Stage 3
        y3v = v + h * (a31 * k1v + a32 * k2v)
        y3w = w + h * (a31 * k1w + a32 * k2w)
        z = y3v
        z2 = z * z
        z3 = z2 * z
        k3v = z - inv3 * z3 - y3w + I
        k3w = ab * y3v - ac * y3w

        # Stage 4
        y4v = v + h * (a41 * k1v + a42 * k2v + a43 * k3v)
        y4w = w + h * (a41 * k1w + a42 * k2w + a43 * k3w)
        z = y4v
        z2 = z * z
        z3 = z2 * z
        k4v = z - inv3 * z3 - y4w + I
        k4w = ab * y4v - ac * y4w

        # Stage 5
        y5v = v + h * (a51 * k1v + a52 * k2v + a53 * k3v + a54 * k4v)
        y5w = w + h * (a51 * k1w + a52 * k2w + a53 * k3w + a54 * k4w)
        z = y5v
        z2 = z * z
        z3 = z2 * z
        k5v = z - inv3 * z3 - y5w + I
        k5w = ab * y5v - ac * y5w

        # Stage 6
        y6v = v + h * (a61 * k1v + a62 * k2v + a63 * k3v + a64 * k4v + a65 * k5v)
        y6w = w + h * (a61 * k1w + a62 * k2w + a63 * k3w + a64 * k4w + a65 * k5w)
        z = y6v
        z2 = z * z
        z3 = z2 * z
        k6v = z - inv3 * z3 - y6w + I
        k6w = ab * y6v - ac * y6w

        # 5th order solution
        y5_v = v + h * (b1 * k1v + b3 * k3v + b4 * k4v + b5 * k5v + b6 * k6v)
        y5_w = w + h * (b1 * k1w + b3 * k3w + b4 * k4w + b5 * k5w + b6 * k6w)

        # 7th stage at (t + h, y5) for FSAL and error estimate
        z = y5_v
        z2 = z * z
        z3 = z2 * z
        k7v = z - inv3 * z3 - y5_w + I
        k7w = ab * y5_v - ac * y5_w

        # Embedded error estimate directly via weights e
        err_v = h * (e1 * k1v + e3 * k3v + e4 * k4v + e5 * k5v + e6 * k6v + e7 * k7v)
        err_w = h * (e1 * k1w + e3 * k3w + e4 * k4w + e5 * k5w + e6 * k6w + e7 * k7w)

        # Scaled RMS error norm
        av = v if v >= 0.0 else -v
        aw = w if w >= 0.0 else -w
        ayv = y5_v if y5_v >= 0.0 else -y5_v
        ayw = y5_w if y5_w >= 0.0 else -y5_w
        scale_v = atol + rtol * (av if av > ayv else ayv)
        scale_w = atol + rtol * (aw if aw > ayw else ayw)
        ev = err_v / scale_v
        ew = err_w / scale_w
        err_norm = (ev * ev + ew * ew) ** 0.5
        err_norm *= INV_SQRT2  # 1/sqrt(2)

        if err_norm <= 1.0:
            # Accept step
            t += h
            v = y5_v
            w = y5_w
            # FSAL: reuse k7 as next k1
            k1v, k1w = k7v, k7w
        # Else: reject step, keep (t, v, w) and reuse k1

        # Step size adaptation using standard exponent -1/ORDER
        if err_norm == 0.0:
            factor = MAX_FACTOR
        else:
            factor = SAFETY * err_norm ** (-1.0 / ORDER)
            if factor < MIN_FACTOR:
                factor = MIN_FACTOR
            elif factor > MAX_FACTOR:
                factor = MAX_FACTOR
        h *= factor

        # Prevent stagnation on tiny step sizes
        ah = h if h >= 0.0 else -h
        if ah < 1e-16:
            break

    return v, w

class Solver:
    __slots__ = ()

    def __init__(self) -> None:
        # Warm up numba compilation outside of solve timing.
        try:
            _integrate_dp45(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1e-8, 1e-8)
        except Exception:
            pass

    def solve(self, problem: Dict[str, Any], **kwargs) -> List[float]:
        # Extract inputs without NumPy overhead
        y0 = problem["y0"]
        v0 = float(y0[0])
        w0 = float(y0[1])
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        params = problem["params"]
        a = float(params["a"])
        b = float(params["b"])
        c = float(params["c"])
        I = float(params["I"])

        # Trivial case
        if t1 == t0:
            return [v0, w0]

        # Tolerances matching reference-level accuracy
        rtol = 1e-8
        atol = 1e-8

        v_final, w_final = _integrate_dp45(t0, t1, v0, w0, a, b, c, I, rtol, atol)
        return [float(v_final), float(w_final)]
EOF
