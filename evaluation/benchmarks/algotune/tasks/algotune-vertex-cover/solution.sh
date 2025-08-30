#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, List

class Solver:
    def solve(self, problem, **kwargs) -> Any:
        """
        Compute a minimum vertex cover of an undirected graph given by its adjacency matrix.

        Input: problem - 2D list (n x n) adjacency matrix with 0/1 entries, symmetric, zero diagonal.
        Output: List of vertex indices in a minimum vertex cover.

        Approach: Solve Maximum Independent Set by finding a Maximum Clique in the complement graph
        using Tomita's coloring-based branch-and-bound (bitset implementation). Then return its
        complement as the minimum vertex cover.
        """
        # Handle trivial cases
        if not problem:
            return []

        n = len(problem)

        # Build original adjacency as bitsets
        adj: List[int] = [0] * n
        for i in range(n):
            row = problem[i]
            m = 0
            for j, v in enumerate(row):
                if v and j != i:
                    m |= 1 << j
            adj[i] = m

        full_mask = (1 << n) - 1

        # Complement graph adjacency (for maximum clique)
        comp_adj: List[int] = [0] * n
        for i in range(n):
            comp_adj[i] = (~adj[i]) & (full_mask ^ (1 << i))

        # Utility: index of least significant set bit
        def lsb_index(x: int) -> int:
            return (x & -x).bit_length() - 1

        ibc = int.bit_count  # local alias for speed

        # Strong greedy heuristic to get an initial clique (on complement graph)
        def greedy_clique_maxdeg(P: int) -> int:
            clique_mask = 0
            cand = P
            while cand:
                # pick vertex with maximum degree within current candidate subgraph
                r = cand
                best_v = -1
                best_deg = -1
                while r:
                    v_bit = r & -r
                    v = v_bit.bit_length() - 1
                    r ^= v_bit
                    d = ibc(comp_adj[v] & cand)
                    if d > best_deg:
                        best_deg = d
                        best_v = v
                clique_mask |= 1 << best_v
                cand &= comp_adj[best_v]
            return clique_mask

        # Strong component-wise solver to reduce problem size and speed up search
        def solve_component(P_mask: int) -> int:
            # Initial lower bound for MIS via a greedy clique in complement restricted to component
            best_clique_mask = greedy_clique_maxdeg(P_mask) & P_mask
            best_size = best_clique_mask.bit_count()

            # Fast bitset-only greedy coloring for upper bounds
            def color_sort(P: int) -> tuple[list[int], list[int]]:
                order: List[int] = []
                colors: List[int] = []
                p = P
                color = 0
                while p:
                    color += 1
                    q = p
                    while q:
                        b = q & -q
                        v = b.bit_length() - 1
                        order.append(v)
                        colors.append(color)
                        p &= ~b
                        q &= ~b
                        q &= ~comp_adj[v]
                return order, colors

            def expand(P: int, cur_mask: int, cur_size: int) -> None:
                nonlocal best_size, best_clique_mask
                if not P:
                    if cur_size > best_size:
                        best_size = cur_size
                        best_clique_mask = cur_mask
                    return

                order, colors = color_sort(P)
                Plocal = P
                for i in range(len(order) - 1, -1, -1):
                    if cur_size + colors[i] <= best_size:
                        return
                    v = order[i]
                    bit = 1 << v
                    expand(Plocal & comp_adj[v], cur_mask | bit, cur_size + 1)
                    Plocal &= ~bit

            expand(P_mask, 0, 0)
            return best_clique_mask

        # Decompose graph into connected components (in the original graph) and solve each
        rem = full_mask
        mis_mask = 0
        while rem:
            b = rem & -rem
            start = b.bit_length() - 1
            # Build component via DFS over original adjacency
            comp = 0
            stack = [start]
            rem &= ~b
            comp |= b
            while stack:
                v = stack.pop()
                nbrs = adj[v] & rem
                while nbrs:
                    nb = nbrs & -nbrs
                    u = nb.bit_length() - 1
                    nbrs ^= nb
                    rem &= ~nb
                    comp |= nb
                    stack.append(u)
            # Solve MIS (as maximum clique in complement) on this component
            mis_mask |= solve_component(comp)

        # Minimum vertex cover is complement of MIS
        cover_mask = full_mask & ~mis_mask
        res: List[int] = []
        r = cover_mask
        while r:
            b = r & -r
            v = b.bit_length() - 1
            res.append(v)
            r ^= b
        res.sort()
        return res
EOF
