# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np



class Task:
    """
    Gale–Shapley proposer-optimal stable matching.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int) -> dict[str, Any]:
        if n < 1:
            raise ValueError("n must be ≥ 1")

        rng = np.random.default_rng(random_seed)
        indices = list(range(n))

        proposer_prefs = {i: rng.permutation(indices).tolist() for i in range(n)}
        receiver_prefs = {i: rng.permutation(indices).tolist() for i in range(n)}

        return {"proposer_prefs": proposer_prefs, "receiver_prefs": receiver_prefs}

    def solve(self, problem: dict[str, Any]) -> dict[str, list[int]]:
        prop_raw = problem["proposer_prefs"]
        recv_raw = problem["receiver_prefs"]

        # normalise to list-of-lists
        if isinstance(prop_raw, dict):
            n = len(prop_raw)
            proposer_prefs = [prop_raw[i] for i in range(n)]
        else:
            proposer_prefs = list(prop_raw)
            n = len(proposer_prefs)

        if isinstance(recv_raw, dict):
            receiver_prefs = [recv_raw[i] for i in range(n)]
        else:
            receiver_prefs = list(recv_raw)

        # receiver ranking tables
        recv_rank = [[0] * n for _ in range(n)]
        for r, prefs in enumerate(receiver_prefs):
            for rank, p in enumerate(prefs):
                recv_rank[r][p] = rank

        next_prop = [0] * n
        recv_match = [None] * n
        free = list(range(n))

        while free:
            p = free.pop(0)
            r = proposer_prefs[p][next_prop[p]]
            next_prop[p] += 1

            cur = recv_match[r]
            if cur is None:
                recv_match[r] = p
            else:
                if recv_rank[r][p] < recv_rank[r][cur]:
                    recv_match[r] = p
                    free.append(cur)
                else:
                    free.append(p)

        matching = [0] * n
        for r, p in enumerate(recv_match):
            matching[p] = r

        return {"matching": matching}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        if "matching" not in solution:
            logging.error("Solution missing 'matching' key.")
            return False

        prop_raw = problem["proposer_prefs"]
        recv_raw = problem["receiver_prefs"]

        if isinstance(prop_raw, dict):
            n = len(prop_raw)
            proposer_prefs = [prop_raw[i] for i in range(n)]
        else:
            proposer_prefs = list(prop_raw)
            n = len(proposer_prefs)

        if isinstance(recv_raw, dict):
            receiver_prefs = [recv_raw[i] for i in range(n)]
        else:
            receiver_prefs = list(recv_raw)

        matching = solution["matching"]
        if not (isinstance(matching, list) and len(matching) == n):
            logging.error("Matching has wrong length or type.")
            return False
        if len(set(matching)) != n or not all(0 <= r < n for r in matching):
            logging.error("Matching is not a permutation of receivers.")
            return False

        # build inverse map
        proposer_to_receiver = matching
        receiver_to_proposer = [0] * n
        for p, r in enumerate(proposer_to_receiver):
            receiver_to_proposer[r] = p

        # stability check: no blocking pair
        for p in range(n):
            p_match_rank = proposer_prefs[p].index(proposer_to_receiver[p])
            for better_r in proposer_prefs[p][:p_match_rank]:
                other_p = receiver_to_proposer[better_r]
                r_prefs = receiver_prefs[better_r]
                if r_prefs.index(p) < r_prefs.index(other_p):
                    logging.error(f"Blocking pair found: proposer {p} and receiver {better_r}.")
                    return False

        return True