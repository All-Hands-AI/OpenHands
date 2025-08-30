# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from sklearn.utils.extmath import randomized_svd



class Task:
    """
    Approximate truncated SVD via randomized algorithms.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(
        self,
        n: int,
        random_seed: int,
        *,
        m: int | None = None,
        n_components: int | None = None,
        matrix_type: str = "low_rank",
        effective_rank: int | None = None,
        condition_number: float = 10.0,
        noise_level: float = 0.1,
        sparsity: float = 0.0,
        decay_factor: float = 0.1,
    ) -> dict[str, Any]:
        rng = np.random.default_rng(random_seed)
        m = m or n
        n_components = n_components or max(1, min(n, m) // 4)

        if matrix_type == "low_rank":
            eff_rank = effective_rank or max(1, min(n, m) // 4)
            A = self._generate_low_rank_matrix(n, m, eff_rank, noise_level, rng)
        elif matrix_type == "sparse":
            A = self._generate_sparse_matrix(n, m, sparsity, rng)
        elif matrix_type == "ill_conditioned":
            A = self._generate_ill_conditioned_matrix(n, m, condition_number, rng)
        elif matrix_type == "exponential_decay":
            A = self._generate_exponential_decay_matrix(n, m, decay_factor, rng)
        elif matrix_type == "block_diagonal":
            A = self._generate_block_diagonal_matrix(n, m, rng)
        elif matrix_type == "random":
            A = rng.standard_normal((n, m))
        else:
            raise ValueError(f"Unknown matrix_type: {matrix_type}")

        return {
            "n_components": n_components,
            "matrix": A,
            "matrix_type": matrix_type,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, list]:
        A = problem["matrix"]
        n_components = problem["n_components"]
        n_iter = 10 if problem["matrix_type"] == "ill_conditioned" else 5

        U, s, Vt = randomized_svd(A, n_components=n_components, n_iter=n_iter, random_state=42)

        return {"U": U, "S": s, "V": Vt.T}

    def is_solution(
        self, problem: dict[str, Any], solution: dict[str, list], *, log: bool = False
    ) -> bool:
        A = problem["matrix"]
        k = problem["n_components"]
        matrix_type = problem["matrix_type"]

        try:
            U = np.asarray(solution["U"], dtype=float)
            s = np.asarray(solution["S"], dtype=float)
            V = np.asarray(solution["V"], dtype=float)
        except Exception as e:
            if log:
                logging.error(f"Conversion error: {e}")
            return False

        n, m = A.shape
        if U.shape != (n, k) or V.shape != (m, k) or s.shape != (k,):
            return False
        if not (np.isfinite(U).all() and np.isfinite(V).all() and np.isfinite(s).all()):
            return False
        if not np.allclose(U.T @ U, np.eye(k), atol=1e-5):
            return False
        if not np.allclose(V.T @ V, np.eye(k), atol=1e-5):
            return False
        if (s < 0).any() or (s[:-1] < s[1:]).any():
            return False

        A_hat = U @ np.diag(s) @ V.T
        rel_err = np.linalg.norm(A - A_hat, "fro") / max(1.0, np.linalg.norm(A, "fro"))

        tol = 0.5
        if matrix_type == "ill_conditioned":
            tol *= 2
        elif matrix_type == "sparse":
            tol *= 1.5
        elif matrix_type == "low_rank":
            tol *= 0.8
        tol *= 1 + max(n, m) / 1000 * 0.5
        tol *= 1 + (1 - k / min(n, m)) * 2

        return bool(rel_err <= tol)

    # ------------------------------------------------------------------ #
    # Matrix generators
    # ------------------------------------------------------------------ #
    @staticmethod
    def _generate_low_rank_matrix(
        n: int, m: int, rank: int, noise_level: float, rng: np.random.Generator
    ) -> np.ndarray:
        rank = min(rank, min(n, m))
        A = rng.standard_normal((n, rank)) @ rng.standard_normal((rank, m))
        if noise_level:
            A += noise_level * rng.standard_normal((n, m))
        return A

    @staticmethod
    def _generate_sparse_matrix(
        n: int, m: int, sparsity: float, rng: np.random.Generator
    ) -> np.ndarray:
        A = rng.standard_normal((n, m))
        mask = rng.random((n, m)) < sparsity
        A[mask] = 0.0
        return A

    @staticmethod
    def _generate_ill_conditioned_matrix(
        n: int, m: int, condition_number: float, rng: np.random.Generator
    ) -> np.ndarray:
        p = min(n, m)
        U, _ = np.linalg.qr(rng.standard_normal((n, p)))
        V, _ = np.linalg.qr(rng.standard_normal((m, p)))
        s = np.logspace(0, -np.log10(condition_number), p)
        return U @ np.diag(s) @ V.T

    @staticmethod
    def _generate_exponential_decay_matrix(
        n: int, m: int, decay_factor: float, rng: np.random.Generator
    ) -> np.ndarray:
        p = min(n, m)
        U, _ = np.linalg.qr(rng.standard_normal((n, p)))
        V, _ = np.linalg.qr(rng.standard_normal((m, p)))
        s = np.exp(-decay_factor * np.arange(p))
        return U @ np.diag(s) @ V.T

    @staticmethod
    def _generate_block_diagonal_matrix(n: int, m: int, rng: np.random.Generator) -> np.ndarray:
        A = np.zeros((n, m))
        p = min(n, m)
        remaining = p
        pos = 0
        while remaining:
            size = rng.integers(1, min(remaining, 10) + 1)
            block = rng.standard_normal((size, size))
            A[pos : pos + size, pos : pos + size] = block
            pos += size
            remaining -= size
        return A