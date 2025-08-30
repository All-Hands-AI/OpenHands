# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
import scipy.sparse
import scipy.sparse.csgraph
from scipy.spatial.distance import cdist



def random_geometric(shape, rng):
    """2-D points → squared-distance cost matrix (CSR)."""
    P = rng.integers(1, 1000, size=(shape[0], 2))
    Q = rng.integers(1, 1000, size=(shape[1], 2))
    return scipy.sparse.csr_matrix(cdist(P, Q, "sqeuclidean"))


class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generator_type = random_geometric

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        rng = np.random.default_rng(random_seed)
        cost = self.generator_type((n, n), rng).astype(float)
        return {
            "data": cost.data.tolist(),
            "indices": cost.indices.tolist(),
            "indptr": cost.indptr.tolist(),
            "shape": cost.shape,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, dict[str, list[int]]]:
        try:
            mat = scipy.sparse.csr_matrix(
                (problem["data"], problem["indices"], problem["indptr"]), shape=problem["shape"]
            )
        except Exception as e:
            logging.error("Rebuild CSR failed: %s", e)
            return {"assignment": {"row_ind": [], "col_ind": []}}

        try:
            # *** FIX: pass matrix positionally, no keyword ***
            row_ind, col_ind = scipy.sparse.csgraph.min_weight_full_bipartite_matching(mat)
        except Exception as e:
            logging.error("Matching failed: %s", e)
            return {"assignment": {"row_ind": [], "col_ind": []}}

        return {"assignment": {"row_ind": row_ind.tolist(), "col_ind": col_ind.tolist()}}

    def is_solution(
        self, problem: dict[str, Any], solution: dict[str, dict[str, list[int]]]
    ) -> bool:
        for k in ("data", "indices", "indptr", "shape"):
            if k not in problem:
                return False
        n, _ = problem["shape"]

        if "assignment" not in solution:
            return False
        row_ind = solution["assignment"].get("row_ind", [])
        col_ind = solution["assignment"].get("col_ind", [])

        if len(row_ind) != n or len(col_ind) != n:
            return False
        if set(row_ind) != set(range(n)) or set(col_ind) != set(range(n)):
            return False

        mat = scipy.sparse.csr_matrix(
            (problem["data"], problem["indices"], problem["indptr"]), shape=(n, n)
        )
        weight_prop = float(sum(mat[i, j] for i, j in zip(row_ind, col_ind)))

        # *** FIX: positional call here as well ***
        ref_row, ref_col = scipy.sparse.csgraph.min_weight_full_bipartite_matching(mat)
        weight_opt = float(sum(mat[i, j] for i, j in zip(ref_row, ref_col)))

        return bool(np.isclose(weight_prop, weight_opt, rtol=1e-5, atol=1e-8))