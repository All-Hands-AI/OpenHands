#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, Dict

import numpy as np
import ot

def _emd_2x2(a: np.ndarray, b: np.ndarray, M: np.ndarray | list) -> np.ndarray | None:
    """
    Closed-form optimal transport for 2x2 case when the solution is unique (c != 0).
    Returns None if tie (c == 0), so caller can fall back to ot.lp.emd to match reference tie-breaking.
    """
    # a = [a1, a2], b = [b1, b2]
    a1, a2 = float(a[0]), float(a[1])
    b1, b2 = float(b[0]), float(b[1])

    # Feasible interval for g11
    lo = max(0.0, a1 - b2)
    hi = min(a1, b1)

    # Extract costs
    if isinstance(M, np.ndarray):
        M00 = float(M[0, 0])
        M01 = float(M[0, 1])
        M10 = float(M[1, 0])
        M11 = float(M[1, 1])
    else:
        M00 = float(M[0][0])
        M01 = float(M[0][1])
        M10 = float(M[1][0])
        M11 = float(M[1][1])

    # Determine which bound minimizes cost
    c = M00 - M01 - M10 + M11
    if c == 0.0:
        return None  # tie; let POT decide to match exactly

    g11 = hi if c < 0.0 else lo
    g12 = a1 - g11
    g21 = b1 - g11
    g22 = a2 - g21

    # Clean extremely small negatives due to floating arithmetic
    tol = 1e-15

    def _clip(x: float) -> float:
        return 0.0 if abs(x) < tol else x

    G = np.array([[ _clip(g11), _clip(g12)],
                  [ _clip(g21), _clip(g22)]], dtype=np.float64)
    return G

def _north_west_corner(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # Construct a feasible (and optimal for Monge) transport plan via the north-west corner rule.
    a_rem = a.astype(np.float64, copy=True)
    b_rem = b.astype(np.float64, copy=True)
    n, m = a_rem.size, b_rem.size
    G = np.zeros((n, m), dtype=np.float64)

    i = 0
    j = 0
    tol = 1e-15
    while i < n and j < m:
        mass = a_rem[i] if a_rem[i] <= b_rem[j] else b_rem[j]
        G[i, j] = mass
        a_rem[i] -= mass
        b_rem[j] -= mass

        ai_zero = a_rem[i] <= tol
        bj_zero = b_rem[j] <= tol
        if ai_zero and bj_zero:
            i += 1
            j += 1
        elif ai_zero:
            i += 1
        elif bj_zero:
            j += 1
        else:
            # Should not happen if sums match and all nonnegative; robustly advance
            j += 1

    return G

def _is_strict_monge_full(M: np.ndarray) -> bool:
    # Full vectorized strict Monge check on all adjacent 2x2 minors.
    if M.shape[0] < 2 or M.shape[1] < 2:
        return True  # Trivially Monge
    A = M[:-1, :-1]
    B = M[1:, 1:]
    C = M[:-1, 1:]
    D = M[1:, :-1]
    scale = float(np.max(np.abs(M)))
    tol = 1e-12 * (scale + 1.0)
    return np.all(A + B <= C + D - tol)

def _is_strict_monge(M: np.ndarray) -> bool:
    # Fast early-exit sampling followed by full check only if sampling passes.
    n, m = M.shape
    if n < 2 or m < 2:
        return True
    nr = n - 1
    mr = m - 1
    total = nr * mr
    # Small cases: do full check
    if total <= 256:
        return _is_strict_monge_full(M)

    # Sampling grid
    scale = float(np.max(np.abs(M)))
    tol = 1e-12 * (scale + 1.0)
    # Choose about 64 samples spread roughly evenly
    target = 64
    si = max(1, nr // int(np.sqrt(target)))
    sj = max(1, mr // int(np.sqrt(target)))
    i = 0
    while i < nr:
        j = 0
        while j < mr:
            if not (M[i, j] + M[i + 1, j + 1] <= M[i, j + 1] + M[i + 1, j] - tol):
                return False
            j += sj
        i += si

    # Passed sampling, confirm with full check to ensure strictness
    return _is_strict_monge_full(M)

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> Any:
        """
        Fast EMD solver that matches POT's ot.lp.emd exactly by:
          - Handling trivial/degenerate cases directly
          - Removing zero-mass rows/columns before calling ot.lp.emd (and expanding back)
          - Using a closed-form 2x2 unique-solution shortcut
          - Using NW corner rule for strictly Monge costs (unique optimal plan)
          - Falling back to ot.lp.emd for general cases

        Returns {"transport_plan": np.ndarray of shape (n, m)}.
        """
        a_in = problem["source_weights"]
        b_in = problem["target_weights"]
        M_in = problem["cost_matrix"]

        # Zero-copy when possible for a and b
        a = a_in if isinstance(a_in, np.ndarray) and a_in.dtype == np.float64 else np.asarray(a_in, dtype=np.float64)
        b = b_in if isinstance(b_in, np.ndarray) and b_in.dtype == np.float64 else np.asarray(b_in, dtype=np.float64)

        n, m = a.shape[0], b.shape[0]

        # Trivial shapes
        if n == 1:
            return {"transport_plan": b.reshape(1, -1)}
        if m == 1:
            return {"transport_plan": a.reshape(-1, 1)}

        # Precompute nonzero indices once to avoid multiple scans
        I = np.flatnonzero(a)
        J = np.flatnonzero(b)

        # If exactly one nonzero in a: unique plan
        if I.size == 1:
            i = int(I[0])
            G = np.zeros((n, m), dtype=np.float64)
            G[i, :] = b
            return {"transport_plan": G}

        # Remove zero-mass rows/columns to speed up LP without changing the solution
        if I.size != n or J.size != m:
            # Reduced problem
            a_r = a[I]
            b_r = b[J]
            # Build reduced cost matrix lazily
            if isinstance(M_in, np.ndarray):
                M_r = M_in[np.ix_(I, J)]
            else:
                M_r = np.asarray(M_in, dtype=np.float64)[np.ix_(I, J)]
            nr, mr = a_r.size, b_r.size

            # Trivial reduced shapes
            if nr == 1:
                G_full = np.zeros((n, m), dtype=np.float64)
                G_full[I[0], J] = b_r
                return {"transport_plan": G_full}
            if mr == 1:
                G_full = np.zeros((n, m), dtype=np.float64)
                G_full[I, J[0]] = a_r
                return {"transport_plan": G_full}

            # 2x2 unique solution closed-form
            if nr == 2 and mr == 2:
                G_r = _emd_2x2(a_r, b_r, M_r)
                if G_r is not None:
                    G_full = np.zeros((n, m), dtype=np.float64)
                    G_full[np.ix_(I, J)] = G_r
                    return {"transport_plan": G_full}

            # General reduced case via POT
            if isinstance(M_r, np.ndarray) and M_r.dtype == np.float64 and M_r.flags.c_contiguous:
                M_cont = M_r
            else:
                M_cont = np.ascontiguousarray(M_r, dtype=np.float64)
            G_r = ot.lp.emd(a_r, b_r, M_cont, check_marginals=False)

            G_full = np.zeros((n, m), dtype=np.float64)
            G_full[np.ix_(I, J)] = G_r
            return {"transport_plan": G_full}

        # No zeros to remove. Try 2x2 unique closed-form
        if n == 2 and m == 2:
            # Pass M_in directly to avoid unnecessary conversion
            G = _emd_2x2(a, b, M_in)
            if G is not None:
                return {"transport_plan": G}

        # Strict Monge: NW rule optimal and unique (only check small problems)
        if n * m <= 256:
            if isinstance(M_in, np.ndarray):
                M_small = M_in
            else:
                M_small = np.asarray(M_in, dtype=np.float64)
            if _is_strict_monge(M_small):
                G = _north_west_corner(a, b)
                return {"transport_plan": G}

        # General case via POT
        # Ensure M is C-contiguous float64 as required by ot.lp.emd
        if isinstance(M_in, np.ndarray) and M_in.dtype == np.float64 and M_in.flags.c_contiguous:
            M = M_in
        else:
            M = np.ascontiguousarray(M_in, dtype=np.float64)

        G = ot.lp.emd(a, b, M, check_marginals=False)
        return {"transport_plan": G}
        return {"transport_plan": G}
EOF
