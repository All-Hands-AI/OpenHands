# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import cvxpy as cp
import numpy as np



class Task:
    """
    Convex quadratic program:

        minimize (1/2) xᵀ P x + qᵀ x
        subject to  G x ≤ h
                    A x  = b
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # -------------------------------------------------------------------------
    # Problem generation (now guaranteed feasible)
    # -------------------------------------------------------------------------
    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        n = max(n, 2)
        rng = np.random.default_rng(random_seed)
        m = p = n // 2

        M = rng.standard_normal((n, n))
        P = M.T @ M  # PSD
        q = rng.standard_normal(n)
        G = rng.standard_normal((m, n))
        A = rng.standard_normal((p, n))

        x_feas = rng.standard_normal(n)
        h = G @ x_feas + np.abs(rng.standard_normal(m))  # strict inequality slack
        b = A @ x_feas

        return {
            "P": P.tolist(),
            "q": q.tolist(),
            "G": G.tolist(),
            "h": h.tolist(),
            "A": A.tolist(),
            "b": b.tolist(),
        }

    # -------------------------------------------------------------------------
    # Solver
    # -------------------------------------------------------------------------
    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        P = np.asarray(problem["P"], float)
        q = np.asarray(problem["q"], float)
        G = np.asarray(problem["G"], float)
        h = np.asarray(problem["h"], float)
        A = np.asarray(problem["A"], float)
        b = np.asarray(problem["b"], float)
        n = P.shape[0]

        P = (P + P.T) / 2
        x = cp.Variable(n)
        objective = 0.5 * cp.quad_form(x, cp.psd_wrap(P)) + q @ x
        constraints = [G @ x <= h, A @ x == b]
        prob = cp.Problem(cp.Minimize(objective), constraints)
        optimal_value = prob.solve(solver=cp.OSQP, eps_abs=1e-8, eps_rel=1e-8)

        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise ValueError(f"Solver failed (status = {prob.status})")

        return {"solution": x.value.tolist(), "objective": float(optimal_value)}

    # -------------------------------------------------------------------------
    # Validator
    # -------------------------------------------------------------------------
    def is_solution(
        self, problem: dict[str, Any], solution: dict[str, list], atol: float = 1e-6
    ) -> bool:
        x = np.asarray(solution.get("solution", []), float)
        if x.ndim != 1:
            return False

        P = np.asarray(problem["P"], float)
        q = np.asarray(problem["q"], float)
        G = np.asarray(problem["G"], float)
        h = np.asarray(problem["h"], float)
        A = np.asarray(problem["A"], float)
        b = np.asarray(problem["b"], float)

        if x.shape[0] != P.shape[0]:
            return False

        # Feasibility
        if (G @ x - h > atol).any():
            return False
        if not np.allclose(A @ x, b, atol=atol):
            return False

        # Optimality: compare objective value to the true optimum
        true_obj = self.solve(problem)["objective"]
        candidate_obj = 0.5 * x @ P @ x + q @ x
        return bool(candidate_obj <= true_obj + 1e-4 * (1 + abs(true_obj)))