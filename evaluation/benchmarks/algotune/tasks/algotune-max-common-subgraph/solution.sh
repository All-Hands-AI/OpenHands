#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, List, Tuple

class Solver:
    def solve(self, problem, **kwargs) -> Any:
        A: List[List[int]] = problem["A"]
        B: List[List[int]] = problem["B"]
        n = len(A)
        m = len(B)
        if n == 0 or m == 0:
            return []

        # Build association (modular product) graph using bitsets
        adj, N = self._build_product_graph_bitset(A, B)
        if N == 0:
            return []

        # Maximum clique on association graph
        best_vertices = self._max_clique_bitset(adj)

        # Convert vertex ids back to (i, p)
        res = [(v // m, v % m) for v in best_vertices]
        return res

    @staticmethod
    def _build_product_graph_bitset(
        A: List[List[int]],
        B: List[List[int]],
    ) -> Tuple[List[int], int]:
        n = len(A)
        m = len(B)
        N = n * m
        if N == 0:
            return [], 0

        # Precompute bit masks for B edges and non-edges for each p
        full_m_mask = (1 << m) - 1
        B_edges_mask = [0] * m
        for p in range(m):
            row = B[p]
            mask = 0
            # build bitset of neighbors (excluding self)
            for q in range(m):
                if q != p and row[q]:
                    mask |= 1 << q
            B_edges_mask[p] = mask
        B_nonedges_mask = [0] * m
        for p in range(m):
            # non-edges: all except edges and self
            B_nonedges_mask[p] = (full_m_mask ^ B_edges_mask[p]) & ~(1 << p)

        # Precompute block replicators for each i over j != i
        # R_edge[i] has 1 at bit position j*m if A[i][j] == 1
        # R_non[i] has 1 at bit position j*m if A[i][j] == 0 and j != i
        block_shift = [1 << (j * m) for j in range(n)]
        R_edge = [0] * n
        R_non = [0] * n
        for i in range(n):
            ri_e = 0
            ri_n = 0
            Ai = A[i]
            for j in range(n):
                if j == i:
                    continue
                if Ai[j]:
                    ri_e |= block_shift[j]
                else:
                    ri_n |= block_shift[j]
            R_edge[i] = ri_e
            R_non[i] = ri_n

        # Build adjacency bitset for each vertex (i, p) -> index v = i*m + p
        adj = [0] * N
        Bedges = B_edges_mask
        Bnon = B_nonedges_mask
        for i in range(n):
            base_i = i * m
            ri_e = R_edge[i]
            ri_n = R_non[i]
            for p in range(m):
                v = base_i + p
                bedge = Bedges[p]
                bnon = Bnon[p]
                # neighbors = OR over j!=i of (Ai[j]? bedge << j*m : bnon << j*m)
                # Using block replicators to aggregate in O(1) big-int ops
                neighbors = bedge * ri_e + bnon * ri_n
                adj[v] = neighbors
        return adj, N

    @staticmethod
    def _max_clique_bitset(adj: List[int]) -> List[int]:
        N = len(adj)
        if N == 0:
            return []

        # Initial candidate set: all vertices
        P0 = (1 << N) - 1

        # Greedy heuristic to get an initial lower bound
        def greedy_clique(Pmask: int) -> Tuple[int, int]:
            clique_mask = 0
            size = 0
            P = Pmask
            while P:
                # pick vertex with maximum degree within current P
                best_v = -1
                best_deg = -1
                Q = P
                while Q:
                    lb = Q & -Q
                    v = lb.bit_length() - 1
                    d = (adj[v] & P).bit_count()
                    if d > best_deg:
                        best_deg = d
                        best_v = v
                    Q &= Q - 1
                if best_v < 0:
                    break
                vb = 1 << best_v
                clique_mask |= vb
                size += 1
                P &= adj[best_v]
            return size, clique_mask

        init_size, init_mask = greedy_clique(P0)
        best_size = init_size
        best_mask = init_mask

        # Tomita-style branch and bound with coloring
        adj_loc = adj  # local ref
        bit_count = int.bit_count

        def color_sort(Pmask: int) -> Tuple[List[int], List[int]]:
            # Returns (order, ubounds) where ubounds[i] is the color (upper bound)
            # assigned to order[i]. Colors increase along the order.
            order: List[int] = []
            ubounds: List[int] = []
            color = 0
            P = Pmask
            while P:
                color += 1
                Q = P
                assigned = 0
                while Q:
                    lb = Q & -Q
                    v = lb.bit_length() - 1
                    order.append(v)
                    ubounds.append(color)
                    assigned |= (1 << v)
                    # Remove v and all its neighbors from Q for this color class
                    Q &= ~adj_loc[v]
                    Q &= ~lb
                # Remove all vertices assigned this color from remaining P
                P &= ~assigned
            return order, ubounds

        # Recursive expansion
        def expand(Pmask: int, current_mask: int, rsize: int) -> None:
            nonlocal best_size, best_mask
            if Pmask == 0:
                if rsize > best_size:
                    best_size = rsize
                    best_mask = current_mask
                return

            order, ub = color_sort(Pmask)

            # Iterate in reverse order for effective pruning
            for idx in range(len(order) - 1, -1, -1):
                v = order[idx]
                vb = 1 << v
                if (Pmask & vb) == 0:
                    continue
                if rsize + ub[idx] <= best_size:
                    return
                Nv = Pmask & adj_loc[v]
                # Optional quick bound
                if rsize + 1 + bit_count(Nv) <= best_size:
                    Pmask &= ~vb
                    continue
                expand(Nv, current_mask | vb, rsize + 1)
                Pmask &= ~vb
                # Another bound: even selecting all remaining cannot beat best
                if rsize + bit_count(Pmask) <= best_size:
                    return

        expand(P0, 0, 0)

        # Extract list of vertices from best_mask
        res: List[int] = []
        M = best_mask
        while M:
            lb = M & -M
            v = lb.bit_length() - 1
            res.append(v)
            M &= M - 1
        return res
EOF
