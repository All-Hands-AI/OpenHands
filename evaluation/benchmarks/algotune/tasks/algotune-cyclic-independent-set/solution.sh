#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, List, Tuple
from itertools import product
import numpy as np

class Solver:
    def __init__(self) -> None:
        # Cache keyed by (n, m)
        self._cache: dict[Tuple[int, int], dict[str, Any]] = {}

    def _get_precomp(self, n: int, m: int) -> dict[str, Any]:
        key = (n, m)
        pre = self._cache.get(key)
        if pre is not None:
            return pre

        # Powers for base-m encoding
        powers_list = [m ** i for i in range(n - 1, -1, -1)]
        powers_np = np.array(powers_list, dtype=np.int32)
        p_times = np.array([m * p for p in powers_list], dtype=np.int32)

        # Neighbor step offsets for [-1,0,1]^n
        steps = np.array(list(product((-1, 0, 1), repeat=n)), dtype=np.int8)  # (3^n, n)
        base_offsets = (steps.astype(np.int32) @ powers_np).astype(np.int32)  # (3^n,)

        # Precompute full adjustment arrays to avoid boolean indexing per call
        adj_zero = [np.where(steps[:, j] == -1, p_times[j], 0).astype(np.int32) for j in range(n)]
        adj_six = [np.where(steps[:, j] == 1, -p_times[j], 0).astype(np.int32) for j in range(n)]

        # Coefficients for priority class
        mod = m - 2  # 5 for m=7
        c = [pow(2, n - 1 - j, mod) for j in range(n)]
        const_offset = sum(c) % mod

        # Precompute class order scoring (depends only on n, m)
        counts = [1, 0, 0, 0, 0]
        t = n - 1
        q, r = divmod(t, 5)
        base_counts = [q, q, q, q, q]
        for k in range(r):
            base_counts[(k + 1) % 5] += 1
        for j in range(n):
            dj = (2 * c[j]) % mod
            inc = [0, 0, 0, 0, 0]
            if dj == 0:
                inc[0] = t
            else:
                for rv in range(5):
                    inc[(dj * rv) % 5] = base_counts[rv]
            new_counts = [0, 0, 0, 0, 0]
            for a in range(5):
                ca = counts[a]
                if ca == 0:
                    continue
                new_counts[(a + 0) % 5] += ca * inc[0]
                new_counts[(a + 1) % 5] += ca * inc[1]
                new_counts[(a + 2) % 5] += ca * inc[2]
                new_counts[(a + 3) % 5] += ca * inc[3]
                new_counts[(a + 4) % 5] += ca * inc[4]
            counts = new_counts
        score_by_class = [0] * mod
        for s in range(mod):
            score_by_class[s] = (
                ((0 + s) % 5) * counts[0]
                + ((1 + s) % 5) * counts[1]
                + ((2 + s) % 5) * counts[2]
                + ((3 + s) % 5) * counts[3]
                + ((4 + s) % 5) * counts[4]
            )
        class_order = sorted(range(mod), key=lambda s: score_by_class[s], reverse=True)

        pre = {
            "powers_list": [int(x) for x in powers_list],
            "base_offsets": base_offsets,
            "adj_zero": adj_zero,
            "adj_six": adj_six,
            "c": c,
            "const_offset": const_offset,
            "class_order": class_order,
        }
        self._cache[key] = pre
        return pre

    def solve(self, problem, **kwargs) -> Any:
        # problem = (num_nodes, n)
        num_nodes, n = problem

        # Handle trivial exponent
        if n == 0:
            return [tuple()]

        # Fallback for non-7 graphs: simple tensor product of a base independent set
        if num_nodes != 7:
            base = list(range(0, num_nodes, 2))
            return [tuple(t) for t in product(base, repeat=n)]

        # For C7^n strong product: optimized greedy with closed-form scoring
        m = num_nodes  # 7
        mod = m - 2  # 5
        N = m ** n

        pre = self._get_precomp(n, m)
        powers_list: List[int] = pre["powers_list"]
        base_offsets: np.ndarray = pre["base_offsets"]
        adj_zero: List[np.ndarray] = pre["adj_zero"]
        adj_six: List[np.ndarray] = pre["adj_six"]
        c: List[int] = pre["c"]
        const_offset: int = pre["const_offset"]
        class_order: List[int] = pre["class_order"]

        # Bucket indices by score class s0 using odometer-style enumeration
        buckets: List[List[int]] = [[] for _ in range(mod)]
        digits = [0] * n
        idx = 0
        s0 = const_offset  # initial class
        while True:
            buckets[s0].append(idx)
            # increment odometer
            i = n - 1
            while i >= 0 and digits[i] == 6:
                digits[i] = 0
                idx -= 6 * powers_list[i]
                s0 += c[i]
                if s0 >= 5:
                    s0 -= 5
                i -= 1
            if i < 0:
                break
            prev = digits[i]
            digits[i] = prev + 1
            idx += powers_list[i]
            if prev < 4:
                s0 += c[i]
                if s0 >= 5:
                    s0 -= 5

        alive = np.ones(N, dtype=np.bool_)
        selected_indices: List[int] = []
        neigh = np.empty_like(base_offsets)  # reusable neighbor buffer

        # Helper: block neighbors of a selected center index using vectorized offsets
        def block_neighbors(center_idx: int) -> None:
            # Reset to base offsets and add center
            neigh[:] = base_offsets
            neigh[:] += np.int32(center_idx)
            # Decode digits and correct wrap-around
            tmp = center_idx
            for j in range(n - 1, -1, -1):
                d = tmp % 7
                tmp //= 7
                if d == 0:
                    neigh[:] += adj_zero[j]
                elif d == 6:
                    neigh[:] += adj_six[j]
            alive[neigh] = False

        # Greedy selection by class priority with lazy deletion
        for cls in class_order:
            for idx in buckets[cls]:
                if not alive[idx]:
                    continue
                selected_indices.append(idx)
                block_neighbors(idx)

        # Decode selected indices to tuples
        solution: List[Tuple[int, ...]] = []
        for idx in selected_indices:
            tmp = idx
            vertex = [0] * n
            for j in range(n - 1, -1, -1):
                vertex[j] = tmp % 7
                tmp //= 7
            solution.append(tuple(vertex))
        return solution
EOF
