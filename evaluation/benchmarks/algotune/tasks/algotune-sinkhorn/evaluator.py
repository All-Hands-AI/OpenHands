# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
import ot



class Task:
    def __init__(self, **kwargs):
        """
        Entropic optimal‑transport task using Sinkhorn iterations.
        """
        super().__init__(**kwargs)

    def generate_problem(
        self, n: int, random_seed: int = 1
    ) -> dict[str, list[float] | list[list[float]] | float | int]:
        if n <= 0:
            raise ValueError("n must be positive")
        rng = np.random.default_rng(random_seed)
        a = np.full(n, 1.0 / n, dtype=np.float64)
        b = np.full(n, 1.0 / n, dtype=np.float64)
        source_points = rng.random((n, 2))
        target_points = rng.random((n, 2))
        M = ot.dist(source_points, target_points, metric="euclidean")
        reg = 1.0
        return {
            "source_weights": a.tolist(),
            "target_weights": b.tolist(),
            "cost_matrix": M.tolist(),
            "reg": reg,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, list[list[float]] | None | str]:
        a = np.array(problem["source_weights"], dtype=np.float64)
        b = np.array(problem["target_weights"], dtype=np.float64)
        M = np.ascontiguousarray(problem["cost_matrix"], dtype=np.float64)
        reg = float(problem["reg"])
        try:
            G = ot.sinkhorn(a, b, M, reg)
            if not np.isfinite(G).all():
                raise ValueError("Non‑finite values in transport plan")
            return {"transport_plan": G, "error_message": None}
        except Exception as exc:
            logging.error("Sinkhorn solve failed: %s", exc)
            return {"transport_plan": None, "error_message": str(exc)}  # type: ignore

    def is_solution(
        self,
        problem: dict[str, Any],
        solution: dict[str, list[list[float]] | np.ndarray | None | str],
    ) -> bool:
        if "transport_plan" not in solution or solution["transport_plan"] is None:
            logging.error("Transport plan missing or None")
            return False
        a = np.array(problem["source_weights"], dtype=np.float64)
        b = np.array(problem["target_weights"], dtype=np.float64)
        n, m = len(a), len(b)
        G_provided = np.asarray(solution["transport_plan"], dtype=np.float64)
        if G_provided.shape != (n, m):
            logging.error("Shape mismatch")
            return False
        if not np.isfinite(G_provided).all():
            logging.error("Non‑finite entries in provided plan")
            return False
        M = np.ascontiguousarray(problem["cost_matrix"], dtype=np.float64)
        reg = float(problem["reg"])
        G_expected = ot.sinkhorn(a, b, M, reg)

        if not np.allclose(G_provided, G_expected, rtol=1e-6, atol=1e-8):
            logging.error("Provided plan differs from reference beyond tolerance")
            return False
        return True