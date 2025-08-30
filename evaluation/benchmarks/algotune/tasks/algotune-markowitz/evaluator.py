# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import cvxpy as cp
import numpy as np



# Reference: https://colab.research.google.com/github/cvxgrp/cvx_short_course/blob/master/book/docs/applications/notebooks/portfolio_optimization.ipynb


class Task:
    """
    Long-only Markowitz portfolio optimisation.

        maximise_w   μᵀw − γ wᵀΣw
        subject to   1ᵀw = 1,   w ≥ 0
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int) -> dict[str, Any]:
        rng = np.random.default_rng(random_seed)

        μ = rng.standard_normal(n) * 0.1 + 0.05  # ≈5 % mean returns
        Z = rng.standard_normal((n, n)) / np.sqrt(n)  # scale keeps Σ modest
        Σ = Z.T @ Z + 1e-4 * np.eye(n)  # PSD + regularisation
        γ = 1.0  # fixed risk aversion

        return {"μ": μ.tolist(), "Σ": Σ.tolist(), "γ": γ}

    def solve(self, problem: dict[str, Any]) -> dict[str, list[float]] | None:
        μ = np.asarray(problem["μ"], dtype=float)
        Σ = np.asarray(problem["Σ"], dtype=float)
        γ = float(problem["γ"])
        n = μ.size

        w = cp.Variable(n)
        obj = cp.Maximize(μ @ w - γ * cp.quad_form(w, cp.psd_wrap(Σ)))
        cons = [cp.sum(w) == 1, w >= 0]
        try:
            cp.Problem(obj, cons).solve()
        except cp.error.SolverError as e:
            logging.error("CVXPY solver error: %s", e)
            return None

        if w.value is None or not np.isfinite(w.value).all():
            logging.warning("No finite solution returned.")
            return None

        return {"w": w.value.tolist()}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        if "w" not in solution:
            return False

        μ = np.asarray(problem["μ"], dtype=float)
        Σ = np.asarray(problem["Σ"], dtype=float)
        γ = float(problem["γ"])
        w = np.asarray(solution["w"], dtype=float)

        n = μ.size
        if w.shape != (n,):
            return False
        if not np.isfinite(w).all():
            return False
        if abs(np.sum(w) - 1.0) > 1e-4:
            return False
        if (w < -1e-6).any():  # allow tiny numerical negatives
            return False

        # objective value of candidate
        obj_candidate = μ @ w - γ * w @ Σ @ w

        # optimal reference via internal solver
        ref = self.solve(problem)
        if ref is None:
            return False
        w_opt = np.asarray(ref["w"])
        obj_opt = μ @ w_opt - γ * w_opt @ Σ @ w_opt

        # candidate should be within 1e-6 of optimal objective
        return bool(obj_candidate + 1e-6 >= obj_opt)