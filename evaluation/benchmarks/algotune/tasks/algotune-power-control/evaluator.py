# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import cvxpy as cp
import numpy as np



# Reference: https://www.cvxpy.org/examples/dgp/power_control.html


class Task:
    """
    Optimal power allocation for an n-link wireless network:

        minimise      Σ P_i
        subject to    P_min ≤ P ≤ P_max
                     SINR_i ≥ S_min  ∀ i

        SINR_i = G_ii P_i / (σ_i + Σ_{k≠i} G_ik P_k)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int) -> dict[str, Any]:
        rng = np.random.default_rng(random_seed)

        G = rng.uniform(0.0, 0.2, (n, n))
        G += np.diag(rng.uniform(0.8, 1.2, n))  # strong direct gains
        σ = rng.uniform(0.1, 0.5, n)
        P_min = rng.uniform(0.05, 0.15, n)
        P_max = rng.uniform(3.0, 7.0, n)

        # build a feasible S_min
        P_feas = rng.uniform(P_min, P_max)
        sinr = np.array(
            [G[i, i] * P_feas[i] / (σ[i] + (G[i] @ P_feas - G[i, i] * P_feas[i])) for i in range(n)]
        )
        S_min = 0.8 * sinr.min()

        return {
            "G": G.tolist(),
            "σ": σ.tolist(),
            "P_min": P_min.tolist(),
            "P_max": P_max.tolist(),
            "S_min": float(S_min),
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        G = np.asarray(problem["G"], float)
        σ = np.asarray(problem["σ"], float)
        P_min = np.asarray(problem["P_min"], float)
        P_max = np.asarray(problem["P_max"], float)
        S_min = float(problem["S_min"])
        n = G.shape[0]

        P = cp.Variable(n, nonneg=True)
        constraints = [P >= P_min, P <= P_max]

        for i in range(n):
            interf = σ[i] + cp.sum(cp.multiply(G[i], P)) - G[i, i] * P[i]
            constraints.append(G[i, i] * P[i] >= S_min * interf)

        prob = cp.Problem(cp.Minimize(cp.sum(P)), constraints)
        prob.solve(solver=cp.ECOS)

        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise ValueError(f"Solver failed (status={prob.status})")

        return {"P": P.value.tolist(), "objective": float(prob.value)}

    def is_solution(
        self,
        problem: dict[str, Any],
        solution: dict[str, list],
        atol: float = 1e-6,
        rtol: float = 1e-6,
    ) -> bool:
        try:
            P_cand = np.asarray(solution["P"], float)
        except Exception:
            return False

        G = np.asarray(problem["G"], float)
        σ = np.asarray(problem["σ"], float)
        P_min = np.asarray(problem["P_min"], float)
        P_max = np.asarray(problem["P_max"], float)
        S_min = float(problem["S_min"])

        if P_cand.shape != P_min.shape or (P_cand < 0).any():
            return False
        if (P_cand - P_min < -atol).any() or (P_cand - P_max > atol).any():
            return False

        sinr_cand = np.array(
            [
                G[i, i] * P_cand[i] / (σ[i] + (G[i] @ P_cand - G[i, i] * P_cand[i]))
                for i in range(len(P_cand))
            ]
        )
        if (sinr_cand - S_min < -atol).any():
            return False

        obj_cand = P_cand.sum()
        try:
            obj_opt = self.solve(problem)["objective"]
        except Exception:
            return False

        return bool(obj_cand <= obj_opt * (1 + rtol) + atol)