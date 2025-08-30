#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from scipy.integrate import solve_ivp

try:
    import numba as nb
except Exception:  # pragma: no cover
    nb = None

 

def _compute_accelerations_python(
    positions: np.ndarray,
    masses: np.ndarray,
    eps2: float,
    accelerations: np.ndarray,
) -> None:
    """Compute accelerations using pairwise symmetric updates (fast, but different order)."""
    n = positions.shape[0]
    # Zero accelerations
    accelerations.fill(0.0)
    for i in range(n):
        xi = positions[i, 0]
        yi = positions[i, 1]
        zi = positions[i, 2]
        mi = masses[i]
        for j in range(i + 1, n):
            rx = positions[j, 0] - xi
            ry = positions[j, 1] - yi
            rz = positions[j, 2] - zi
            r2 = rx * rx + ry * ry + rz * rz + eps2
            inv_r = 1.0 / np.sqrt(r2)
            inv_r3 = inv_r / r2  # 1 / r^3
            mj = masses[j]
            s_i = mj * inv_r3
            s_j = mi * inv_r3
            # i gets + s_i * r_ij
            accelerations[i, 0] += s_i * rx
            accelerations[i, 1] += s_i * ry
            accelerations[i, 2] += s_i * rz
            # j gets + s_j * r_ji = - s_j * r_ij
            accelerations[j, 0] -= s_j * rx
            accelerations[j, 1] -= s_j * ry
            accelerations[j, 2] -= s_j * rz

def _compute_accelerations_python_ref(
    positions: np.ndarray,
    masses: np.ndarray,
    eps2: float,
    accelerations: np.ndarray,
) -> None:
    """Compute accelerations mirroring the reference i/j loop order for numerical agreement."""
    n = positions.shape[0]
    for i in range(n):
        xi = positions[i, 0]
        yi = positions[i, 1]
        zi = positions[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        for j in range(n):
            if i == j:
                continue
            rx = positions[j, 0] - xi
            ry = positions[j, 1] - yi
            rz = positions[j, 2] - zi
            r2 = rx * rx + ry * ry + rz * rz + eps2
            dist = np.sqrt(r2)
            factor = masses[j] / (r2 * dist)
            ax += factor * rx
            ay += factor * ry
            az += factor * rz
        accelerations[i, 0] = ax
        accelerations[i, 1] = ay
        accelerations[i, 2] = az

if nb is not None:
    @nb.njit(cache=True)  # no fastmath to mimic reference arithmetic order closely
    def _compute_accelerations_numba_ref(
        positions: np.ndarray,
        masses: np.ndarray,
        eps2: float,
        accelerations: np.ndarray,
    ) -> None:
        n = positions.shape[0]
        for i in range(n):
            xi = positions[i, 0]
            yi = positions[i, 1]
            zi = positions[i, 2]
            ax = 0.0
            ay = 0.0
            az = 0.0
            for j in range(n):
                if i != j:
                    rx = positions[j, 0] - xi
                    ry = positions[j, 1] - yi
                    rz = positions[j, 2] - zi
                    r2 = rx * rx + ry * ry + rz * rz + eps2
                    dist = np.sqrt(r2)
                    factor = masses[j] / (r2 * dist)
                    ax += factor * rx
                    ay += factor * ry
                    az += factor * rz
            accelerations[i, 0] = ax
            accelerations[i, 1] = ay
            accelerations[i, 2] = az
else:
    _compute_accelerations_numba_ref = None  # type: ignore

class Solver:
    def __init__(self) -> None:
        # Warm up numba-compiled kernels so JIT time is not counted in solve()
        try:
            if _compute_accelerations_numba_ref is not None:
                _pos = np.zeros((2, 3), dtype=np.float64)
                _mass = np.array([1.0, 1.0], dtype=np.float64)
                _acc = np.empty((2, 3), dtype=np.float64)
                _compute_accelerations_numba_ref(_pos, _mass, 1e-12, _acc)
        except Exception:
            pass
    @staticmethod
    def _rhs_factory(masses: np.ndarray, softening: float, num_bodies: int):
        eps2 = float(softening) ** 2
        masses = masses.astype(np.float64, copy=False)

        # Prefer reference-order kernel (Numba if available) for best numerical match
        accel_kernel = (
            _compute_accelerations_numba_ref
            if _compute_accelerations_numba_ref is not None
            else _compute_accelerations_python_ref
        )

        # Persistent buffers to reduce allocations
        acc_buf = np.empty((num_bodies, 3), dtype=np.float64)
        deriv_buf = np.empty(num_bodies * 6, dtype=np.float64)

        def rhs(t: float, y: np.ndarray) -> np.ndarray:
            # y = [pos(3N), vel(3N)]
            n3 = num_bodies * 3
            positions = y[:n3].reshape(num_bodies, 3)

            # Derivative of positions is velocity (avoid extra reshape)
            deriv_buf[:n3] = y[n3:]

            # Compute accelerations into buffer
            accel_kernel(positions, masses, eps2, acc_buf)

            # Velocity derivatives = accelerations
            deriv_buf[n3:] = acc_buf.reshape(-1)

            # Return a fresh array to avoid aliasing with SciPy internals
            return deriv_buf.copy()

        return rhs

    def solve(self, problem: Dict[str, Any], **kwargs) -> List[float]:
        # Extract inputs
        y0 = np.array(problem["y0"], dtype=np.float64, copy=True)
        t0 = float(problem["t0"])
        t1 = float(problem["t1"])
        masses = np.array(problem["masses"], dtype=np.float64, copy=False)
        softening = float(problem["softening"])
        num_bodies = int(problem["num_bodies"])

        if t1 == t0:
            return y0.tolist()

        rhs = self._rhs_factory(masses, softening, num_bodies)

        # Use a higher-order explicit method for fewer RHS evaluations
        method = "RK45"
        rtol = 1e-8
        atol = 1e-8

        sol = solve_ivp(
            rhs,
            (t0, t1),
            y0,
            method=method,
            rtol=rtol,
            atol=atol,
            vectorized=False,
            t_eval=None,
            dense_output=False,
        )

        if not sol.success:
            raise RuntimeError(f"Solver failed: {sol.message}")

        return sol.y[:, -1].tolist()
EOF
