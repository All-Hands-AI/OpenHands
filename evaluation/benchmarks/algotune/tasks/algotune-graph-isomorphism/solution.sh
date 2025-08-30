#!/bin/bash

cat > /workspace/solver.py << 'EOF'
# -*- coding: utf-8 -*-
"""
Fast graph‑isomorphism solver.

Implements a lightweight back‑tracking algorithm with degree‑based pruning.
For typical isomorphic inputs this is faster than NetworkX's VF2 matcher
while still guaranteeing a correct mapping.
"""

from typing import Any, List, Dict, Set

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, List[int]]:
        """
        Return a node mapping from G1 to G2 that preserves adjacency.

        Parameters
        ----------
        problem : dict
            {
                "num_nodes": int,
                "edges_g1": List[[int, int]],
                "edges_g2": List[[int, int]],
            }

        Returns
        -------
        dict
            {"mapping": List[int]} where mapping[u] = v.
        """
        n: int = problem["num_nodes"]
        edges_g1: List[List[int]] = problem["edges_g1"]
        edges_g2: List[List[int]] = problem["edges_g2"]

        # ------------------------------------------------------------------
        # Build adjacency sets for fast look‑up
        # ------------------------------------------------------------------
        adj1: List[Set[int]] = [set() for _ in range(n)]
        adj2: List[Set[int]] = [set() for _ in range(n)]
        for u, v in edges_g1:
            adj1[u].add(v)
            adj1[v].add(u)
        for x, y in edges_g2:
            adj2[x].add(y)
            adj2[y].add(x)

        # ------------------------------------------------------------------
        # Pre‑compute node degrees – they must match under any isomorphism
        # ------------------------------------------------------------------
        deg1: List[int] = [len(adj1[i]) for i in range(n)]
        deg2: List[int] = [len(adj2[i]) for i in range(n)]

        # Group G2 nodes by degree for quick candidate lookup
        degree_buckets: Dict[int, List[int]] = {}
        for v in range(n):
            degree_buckets.setdefault(deg2[v], []).append(v)

        # ------------------------------------------------------------------
        # Order G1 nodes – nodes with fewer candidates first (helps pruning)
        # ------------------------------------------------------------------
        # For each node in G1 compute number of possible G2 matches (same degree)
        candidate_counts: List[int] = [len(degree_buckets.get(deg1[i], [])) for i in range(n)]
        order: List[int] = sorted(range(n), key=lambda i: candidate_counts[i])

        # ------------------------------------------------------------------
        # Backtracking search
        # ------------------------------------------------------------------
        mapping: List[int] = [-1] * n          # G1 -> G2
        used: List[bool] = [False] * n        # G2 nodes already taken
        found: bool = False

        def dfs(idx: int) -> bool:
            """Return True when a complete mapping is found."""
            if idx == n:
                return True  # all nodes assigned

            u = order[idx]
            possible_vs = degree_buckets.get(deg1[u], [])
            for v in possible_vs:
                if used[v]:
                    continue
                # Consistency check with already assigned neighbours
                ok = True
                for w in adj1[u]:
                    mw = mapping[w]
                    if mw != -1:  # neighbour already mapped
                        if v not in adj2[mw]:
                            ok = False
                            break
                if not ok:
                    continue

                # assign and recurse
                mapping[u] = v
                used[v] = True
                if dfs(idx + 1):
                    return True
                # backtrack
                mapping[u] = -1
                used[v] = False
            return False

        # The problem guarantees an isomorphism, so dfs will succeed
        dfs(0)

        return {"mapping": mapping}
EOF
