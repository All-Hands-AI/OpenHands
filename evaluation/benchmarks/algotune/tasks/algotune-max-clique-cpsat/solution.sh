#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, List

class Solver:
    def solve(self, problem, **kwargs) -> Any:  # noqa: D401
        """
        Solve the Maximum Clique problem.

        Uses a fast exact branch-and-bound algorithm (Tomita-style) with
        greedy coloring for strong upper bounds and bitset operations for speed.

        :param problem: 2D adjacency matrix (list of lists with 0/1).
        :return: List of node indices forming a maximum clique.
        """
        # Basic validation and trivial cases
        if problem is None:
            return []
        n = len(problem)
        if n == 0:
            return []
        if n == 1:
            return [0]

        # Build degrees and check trivial structures
        deg = [0] * n
        for i, row in enumerate(problem):
            # Count neighbors (ignore self-loops)
            cnt = 0
            for j, v in enumerate(row):
                if i != j and v:
                    cnt += 1
            deg[i] = cnt

        # If graph is complete, return all vertices
        if all(d == n - 1 for d in deg):
            return list(range(n))
        # If no edges, any single vertex is a maximum clique
        if max(deg) == 0:
            return [0]

        # Reorder vertices by non-increasing degree for better pruning
        order = sorted(range(n), key=lambda i: deg[i], reverse=True)
        pos = [0] * n
        for new_idx, old_idx in enumerate(order):
            pos[old_idx] = new_idx

        # Build bitset adjacency in the new indexing
        adj: List[int] = [0] * n
        for new_i, old_i in enumerate(order):
            bits = 0
            row = problem[old_i]
            for old_j, val in enumerate(row):
                if old_j != old_i and val:
                    bits |= 1 << pos[old_j]
            adj[new_i] = bits

        # Helpers
        def popcount(x: int) -> int:
            return x.bit_count()

        def lsb_index(x: int) -> int:
            # Index (0-based) of least significant set bit
            return (x & -x).bit_length() - 1

        # Greedy heuristic for initial lower bound
        def greedy_clique() -> List[int]:
            P = (1 << n) - 1
            if P == 0:
                return []
            # pick vertex with max degree in adj
            max_d = -1
            start = 0
            m = P
            while m:
                v = lsb_index(m)
                m &= m - 1
                d = popcount(adj[v])
                if d > max_d:
                    max_d = d
                    start = v
            clique = [start]
            P &= adj[start]
            while P:
                # pick vertex with most connections within P
                best_v = -1
                best_d = -1
                mm = P
                while mm:
                    v = lsb_index(mm)
                    mm &= mm - 1
                    d = popcount(adj[v] & P)
                    if d > best_d:
                        best_d = d
                        best_v = v
                clique.append(best_v)
                P &= adj[best_v]
            return clique

        best_clique: List[int] = greedy_clique()
        best_size = len(best_clique)

        # Greedy coloring to produce an order and bounds
        def color_sort(P: int) -> tuple[list[int], list[int]]:
            order_: List[int] = []
            bounds_: List[int] = []
            if P == 0:
                return order_, bounds_
            U = P
            color = 0
            while U:
                color += 1
                Q = U
                while Q:
                    v = lsb_index(Q)
                    # remove v from Q
                    Q &= Q - 1
                    # assign color to v
                    order_.append(v)
                    bounds_.append(color)
                    # remove neighbors from Q to keep an independent set
                    Q &= ~adj[v]
                    # mark v as colored
                    U &= ~(1 << v)
            return order_, bounds_

        # Branch and bound
        R_list: List[int] = []

        def expand(P: int) -> None:
            nonlocal best_size, best_clique
            order_, bounds_ = color_sort(P)
            # iterate vertices in reverse (highest color first)
            for idx in range(len(order_) - 1, -1, -1):
                v = order_[idx]
                # Bound pruning
                if len(R_list) + bounds_[idx] <= best_size:
                    return
                # include v
                R_list.append(v)
                P_v = P & adj[v]
                if P_v:
                    expand(P_v)
                else:
                    # maximal clique found
                    if len(R_list) > best_size:
                        best_size = len(R_list)
                        best_clique = R_list.copy()
                # backtrack
                R_list.pop()
                # remove v from P for subsequent iterations
                P &= ~(1 << v)

        all_vertices = (1 << n) - 1
        expand(all_vertices)

        # Map back to original indices and return sorted
        res = [order[v] for v in best_clique]
        res.sort()
        return res
EOF
