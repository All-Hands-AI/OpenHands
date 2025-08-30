#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict, List
import time
import sys
import math
from fractions import Fraction
from ortools.sat.python import cp_model

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> List[int]:
        """
        Maximum Weighted Independent Set (MWIS).

        Strategy:
        - For n <= bb_threshold run a branch-and-bound on bitsets by finding
          a maximum-weight clique in the complement graph. Uses vertex
          permutation so high-weight vertices get low bit indices (LSB-first),
          greedy coloring for upper bounds, and LSB iteration to avoid scanning.
        - For larger graphs, fall back to OR-Tools CP-SAT.

        Optional kwargs:
            - time_limit: float seconds to limit B&B search (will return best found).
            - num_workers: int number of CP-SAT workers for fallback.
            - bb_threshold: int to override branching threshold (default 70).
        """
        adj = problem.get("adj_matrix", [])
        weights = problem.get("weights", [])
        n = len(weights)
        if n == 0:
            return []

        # Parse time limit
        time_limit = kwargs.get("time_limit", None)
        try:
            time_limit = float(time_limit) if time_limit is not None else None
        except Exception:
            time_limit = None
        start_time = time.time()

        # Convert weights to floats for B&B
        w_float: List[float] = []
        for w in weights:
            try:
                w_float.append(float(w))
            except Exception:
                w_float.append(float(str(w)))

        # Prepare integer weights for CP-SAT fallback
        all_int = all(abs(w - round(w)) < 1e-12 for w in w_float)
        if all_int:
            w_int = [int(round(w)) for w in w_float]
        else:
            try:
                fracs = [Fraction(str(w)).limit_denominator(10**6) for w in weights]
                denom = 1
                for f in fracs:
                    denom = denom * f.denominator // math.gcd(denom, f.denominator)
                    if denom > 1_000_000:
                        denom = 1000
                        break
                w_int = [int(f * denom) for f in fracs]
            except Exception:
                w_int = [int(round(w * 1000)) for w in w_float]

        # Branch-and-bound threshold
        bb_threshold = kwargs.get("bb_threshold", 70)
        try:
            bb_threshold = int(bb_threshold)
        except Exception:
            bb_threshold = 70

        # For large graphs, use CP-SAT fallback to avoid exponential search
        if n > bb_threshold:
            model = cp_model.CpModel()
            nodes = [model.NewBoolVar(f"x_{i}") for i in range(n)]
            for i in range(n):
                row = adj[i] if i < len(adj) else [0] * n
                for j in range(i + 1, n):
                    val = row[j] if j < len(row) else 0
                    if val:
                        model.Add(nodes[i] + nodes[j] <= 1)
            model.Maximize(sum(w_int[i] * nodes[i] for i in range(n)))
            solver = cp_model.CpSolver()
            if time_limit is not None:
                try:
                    solver.parameters.max_time_in_seconds = float(time_limit)
                except Exception:
                    pass
            workers = kwargs.get("num_workers", 8)
            try:
                solver.parameters.num_search_workers = int(workers)
            except Exception:
                pass
            status = solver.Solve(model)
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                res = [i for i in range(n) if solver.Value(nodes[i]) == 1]
                res.sort()
                return res
            return []

        # Build original adjacency masks (handle ragged rows)
        full_mask = (1 << n) - 1
        orig_adj_mask = [0] * n
        for i in range(n):
            row = adj[i] if i < len(adj) else [0] * n
            m = 0
            for j in range(min(len(row), n)):
                if row[j]:
                    m |= (1 << j)
            orig_adj_mask[i] = m

        # Quick trivial case: no edges -> take all positive-weight nodes
        if all(m == 0 for m in orig_adj_mask):
            res = [i for i, w in enumerate(w_float) if w > 0]
            res.sort()
            return res

        # Complement graph adjacency (we search maximum-weight clique here)
        comp_adj = [0] * n
        for i in range(n):
            comp_adj[i] = (~orig_adj_mask[i]) & full_mask & ~(1 << i)

        # Heuristic ordering: descending weight, tie-break by complement degree
        comp_deg = [comp_adj[i].bit_count() for i in range(n)]
        order_by_weight = sorted(range(n), key=lambda v: (w_float[v], comp_deg[v]), reverse=True)

        # Permute vertices so high-weight vertices have low indices (LSB-first)
        perm = order_by_weight[:]  # new_index -> old_index
        inv = [0] * n  # old_index -> new_index
        for newpos, old in enumerate(perm):
            inv[old] = newpos

        # Permute complement adjacency masks into new indices
        comp_adj_perm = [0] * n
        for old in range(n):
            newpos = inv[old]
            m = comp_adj[old]
            nm = 0
            while m:
                lsb = m & -m
                j = lsb.bit_length() - 1
                nm |= (1 << inv[j])
                m ^= lsb
            comp_adj_perm[newpos] = nm

        # Permute weights
        w_local = [0.0] * n
        for old in range(n):
            w_local[inv[old]] = w_float[old]

        # Bound cache for coloring
        bound_cache: Dict[int, float] = {}

        comp_adj_local = comp_adj_perm
        FULL = (1 << n) - 1
        EPS = 1e-12

        def color_bound(mask: int) -> float:
            """Greedy coloring bound: sum of max weights per color (independent sets)."""
            if mask == 0:
                return 0.0
            if mask in bound_cache:
                return bound_cache[mask]
            color_masks: List[int] = []
            color_max: List[float] = []
            m = mask
            # iterate vertices in increasing index order (which is descending weight)
            while m:
                lsb = m & -m
                v = lsb.bit_length() - 1
                m ^= lsb
                av = comp_adj_local[v]
                placed = False
                for idx, cmask in enumerate(color_masks):
                    # can place v in this color if it has no edges to members (independent)
                    if (av & cmask) == 0:
                        color_masks[idx] = cmask | (1 << v)
                        if w_local[v] > color_max[idx]:
                            color_max[idx] = w_local[v]
                        placed = True
                        break
                if not placed:
                    color_masks.append(1 << v)
                    color_max.append(w_local[v])
            ub = sum(color_max)
            bound_cache[mask] = ub
            return ub

        # Greedy initial clique (warm start) - only take positive weight vertices
        def greedy_initial():
            mask = FULL
            chosen = 0
            total = 0.0
            while mask:
                lsb = mask & -mask
                v = lsb.bit_length() - 1
                # choose only if positive weight
                if w_local[v] > 0:
                    chosen |= (1 << v)
                    total += w_local[v]
                    mask &= comp_adj_local[v]
                else:
                    # skip v
                    mask ^= (1 << v)
            return chosen, total

        best_mask = 0
        best_weight = 0.0  # allow empty set as valid solution with weight 0
        gm, gw = greedy_initial()
        if gw > best_weight:
            best_weight = gw
            best_mask = gm

        sys.setrecursionlimit(10000)

        # Main recursive expansion using LSB iteration
        def expand(mask: int, cur_weight: float, cur_mask: int):
            nonlocal best_weight, best_mask
            # Respect time limit if provided
            if time_limit is not None and (time.time() - start_time) > time_limit:
                return
            ub = cur_weight + color_bound(mask)
            if ub <= best_weight + EPS:
                return
            sub = mask
            # iterate candidates LSB-first (highest priority first due to permutation)
            while sub:
                lsb = sub & -sub
                v = lsb.bit_length() - 1
                sub ^= lsb
                mv = 1 << v
                new_mask = mask & comp_adj_local[v]
                new_weight = cur_weight + w_local[v]
                if new_weight + color_bound(new_mask) > best_weight + EPS:
                    if new_mask == 0:
                        if new_weight > best_weight + EPS:
                            best_weight = new_weight
                            best_mask = cur_mask | mv
                    else:
                        expand(new_mask, new_weight, cur_mask | mv)
                # exclude v from mask for remaining iterations and pruning
                mask ^= mv
                if cur_weight + color_bound(mask) <= best_weight + EPS:
                    return

        expand(FULL, 0.0, 0)

        # Map best_mask (permuted indices) back to original indices
        result = [perm[i] for i in range(n) if (best_mask >> i) & 1]
        result.sort()
        return result
EOF
