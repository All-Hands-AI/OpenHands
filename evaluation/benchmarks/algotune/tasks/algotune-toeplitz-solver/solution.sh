#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any

import numpy as np

try:
    from scipy.linalg import solve_toeplitz as _solve_toeplitz  # type: ignore[assignment]
    try:
        from inspect import signature as _sig_st  # type: ignore
        _ST_HAS_CHECK_FINITE = "check_finite" in _sig_st(_solve_toeplitz).parameters  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        _ST_HAS_CHECK_FINITE = True
except Exception:  # pragma: no cover
    _solve_toeplitz = None  # type: ignore[assignment]
    _ST_HAS_CHECK_FINITE = False

try:
    from scipy.linalg import solveh_toeplitz as _solveh_toeplitz  # type: ignore[assignment]
    try:
        from inspect import signature as _sig_sht  # type: ignore
        _SHT_HAS_CHECK_FINITE = "check_finite" in _sig_sht(_solveh_toeplitz).parameters  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        _SHT_HAS_CHECK_FINITE = True
except Exception:  # pragma: no cover
    _solveh_toeplitz = None  # type: ignore[assignment]
    _SHT_HAS_CHECK_FINITE = False

class Solver:
    def solve(self, problem: dict[str, list[float]] | dict, **kwargs: Any) -> list[float]:
        """
        Solve the linear system T x = b for a Toeplitz matrix defined by first column c and first row r.
        """
        # Convert once to arrays (SciPy will need arrays anyway)
        c_arr = np.asarray(problem["c"], dtype=float)
        r_arr = np.asarray(problem["r"], dtype=float)
        b_arr = np.asarray(problem["b"], dtype=float)

        n = b_arr.shape[0]
        if n == 0:
            return []
        if n == 1:
            return [float(b_arr[0] / c_arr[0])]
        # Zero RHS fast-path
        if not np.any(b_arr):
            return [0.0] * n

        # 2x2 direct solve (T = [[c0, r1],[c1, c0]])
        if n == 2:
            c0 = c_arr[0]
            c1 = c_arr[1]
            r1 = r_arr[1]
            det = c0 * c0 - c1 * r1
            if det != 0:
                inv = 1.0 / det
                x0 = (b_arr[0] * c0 - b_arr[1] * r1) * inv
                x1 = (b_arr[1] * c0 - b_arr[0] * c1) * inv
                return [float(x0), float(x1)]
            # fall through to general solvers if singular/ill-conditioned

        # Very small systems: explicit dense solve can be faster than SciPy overhead
        if n <= 8:
            T = _build_toeplitz(c_arr, r_arr)
            x = np.linalg.solve(T, b_arr)
            return x.tolist()

        # Prefer symmetric/Hermitian Toeplitz solver if available and applicable.
        ht = _solveh_toeplitz
        if ht is not None and np.array_equal(c_arr, r_arr):
            if _SHT_HAS_CHECK_FINITE:
                x = ht(c_arr, b_arr, check_finite=False)  # type: ignore[call-arg]
            else:
                x = ht(c_arr, b_arr)
            return x.tolist()

        st = _solve_toeplitz
        if st is not None:
            if _ST_HAS_CHECK_FINITE:
                x = st((c_arr, r_arr), b_arr, check_finite=False)  # type: ignore[call-arg]
            else:
                x = st((c_arr, r_arr), b_arr)
            return x.tolist()

        # Fallback (rare): build T explicitly and solve with dense solver.
        T = _build_toeplitz(c_arr, r_arr)
        x = np.linalg.solve(T, b_arr)
        return x.tolist()

def _build_toeplitz(c: np.ndarray, r: np.ndarray) -> np.ndarray:
    n = c.shape[0]
    idx = np.arange(n)
    k = idx[:, None] - idx[None, :]
    T = np.empty((n, n), dtype=np.result_type(c, r))
    mask = k >= 0
    T[mask] = c[k[mask]]
    T[~mask] = r[(-k)[~mask]]
    return T
EOF
