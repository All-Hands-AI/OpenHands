# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh



class Task:
    """
    Return the k smallest eigenvalues of a sparse symmetric
    positive‑definite matrix.

    •  Uses Lanczos (`eigsh`) with `which="SM"` to avoid the shift‑invert
       code path that can raise ``ValueError: inconsistent shapes`` on
       older SciPy versions.
    •  Falls back to dense ``eigvalsh`` when the matrix is very small or
       if Lanczos fails to converge.
    """

    # ------------------------------------------------------------------ #
    # Problem generation                                                 #
    # ------------------------------------------------------------------ #
    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        density = 0.01
        default_k = 5

        rng = np.random.default_rng(random_seed)
        mat = sparse.random(
            n,
            n,
            density=density,
            format="csr",
            data_rvs=rng.standard_normal,
        )
        # Make SPD:  A = BᵀB + 10 * sparse.diags(np.abs(rng.standard_normal(n)), format="csr")
        mat = mat.T @ mat + 10 * sparse.diags(np.abs(rng.standard_normal(n)), format="csr")

        # Ensure 1 ≤ k < n (eigsh requirement)
        k = min(default_k, max(1, n - 1))
        return {"matrix": mat, "k": k}

    # ------------------------------------------------------------------ #
    # Solver                                                             #
    # ------------------------------------------------------------------ #
    def solve(self, problem: dict[str, Any]) -> list[float]:
        mat: sparse.spmatrix = problem["matrix"].asformat("csr")
        k: int = int(problem["k"])
        n = mat.shape[0]

        # Dense path for tiny systems or k too close to n
        if k >= n or n < 2 * k + 1:
            vals = np.linalg.eigvalsh(mat.toarray())
            return [float(v) for v in vals[:k]]

        # Sparse Lanczos without shift‑invert
        try:
            vals = eigsh(
                mat,
                k=k,
                which="SM",  # smallest magnitude eigenvalues
                return_eigenvectors=False,
                maxiter=n * 200,
                ncv=min(n - 1, max(2 * k + 1, 20)),  # ensure k < ncv < n
            )
        except Exception:
            # Last‑resort dense fallback (rare)
            vals = np.linalg.eigvalsh(mat.toarray())[:k]

        return [float(v) for v in np.sort(np.real(vals))]

    # ------------------------------------------------------------------ #
    # Validator                                                          #
    # ------------------------------------------------------------------ #
    def is_solution(self, problem: dict[str, Any], solution: list[float]) -> bool:
        k = int(problem["k"])
        mat: sparse.spmatrix = problem["matrix"]
        n = mat.shape[0]

        # Basic type / length check
        if not isinstance(solution, list) or len(solution) != k:
            return False

        # Convert to floats and check finiteness
        try:
            sol_sorted = sorted(float(np.real(s)) for s in solution)
        except Exception:
            return False
        if not all(np.isfinite(sol_sorted)):
            return False

        # Reference computation (same logic as in solve)
        if k >= n or n < 2 * k + 1:
            ref_vals = np.linalg.eigvalsh(mat.toarray())[:k]
        else:
            try:
                ref_vals = eigsh(
                    mat,
                    k=k,
                    which="SM",
                    return_eigenvectors=False,
                    maxiter=n * 200,
                    ncv=min(n - 1, max(2 * k + 1, 20)),
                )
            except Exception:
                ref_vals = np.linalg.eigvalsh(mat.toarray())[:k]

        ref_sorted = sorted(float(v) for v in np.real(ref_vals))

        # Accept if maximum relative error ≤ 1 × 10⁻⁶
        rel_err = max(abs(a - b) / max(abs(b), 1e-12) for a, b in zip(sol_sorted, ref_sorted))
        return rel_err <= 1e-6

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)