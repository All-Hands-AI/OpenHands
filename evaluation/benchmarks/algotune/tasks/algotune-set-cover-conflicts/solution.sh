#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import sys
from typing import Any, List
try:
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    SAT_AVAILABLE = True
except ImportError:
    SAT_AVAILABLE = False
class Solver:
    def solve(self, problem: Any, **kwargs) -> List[int]:
        # Unpack problem
        n, sets, conflicts, *rest = problem
        m = len(sets)
        # Precompute coverage bitmasks
        coverage = [0] * m
        for i, s in enumerate(sets):
            mask = 0
            for obj in s:
                mask |= 1 << obj
            coverage[i] = mask
        full_mask = (1 << n) - 1

        # Precompute covers_by: for each object, list of sets covering it
        covers_by = [[] for _ in range(n)]
        for i, mask in enumerate(coverage):
            msk = mask
            while msk:
                lsb = msk & -msk
                obj = lsb.bit_length() - 1
                covers_by[obj].append(i)
                msk ^= lsb
        # Use SAT solver if available (quick early exit)
        if SAT_AVAILABLE:
            wcnf = WCNF()
            for o in range(n):
                wcnf.append([i+1 for i in covers_by[o]])
            for group in conflicts:
                for ii in range(len(group)):
                    for jj in range(ii+1, len(group)):
                        wcnf.append([-(group[ii]+1), -(group[jj]+1)])
            for i in range(m):
                wcnf.append([-(i+1)], weight=1)
            rc2 = RC2(wcnf)
            model = rc2.compute()
            return [i for i in range(m) if (i+1) in model]
        # Precompute covers_by_mask for dynamic candidate computation
        covers_by_mask = [0] * n
        for obj in range(n):
            msk2 = 0
            for i in covers_by[obj]:
                msk2 |= 1 << i
            covers_by_mask[obj] = msk2
        # Precompute conflict adjacency masks
        conflict_adj = [0] * m
        for group in conflicts:
            cmask = 0
            for i in group:
                cmask |= 1 << i
            for i in group:
                conflict_adj[i] |= cmask

        # Use SAT solver if available
        if SAT_AVAILABLE:
            wcnf = WCNF()
            # Hard cover clauses
            for o in range(n):
                wcnf.append([i+1 for i in covers_by[o]])
            # Hard conflict clauses
            for group in conflicts:
                for ii in range(len(group)):
                    for jj in range(ii+1, len(group)):
                        wcnf.append([-(group[ii]+1), -(group[jj]+1)])
            # Soft minimize sets
            for i in range(m):
                wcnf.append([-(i+1)], weight=1)
            rc2 = RC2(wcnf)
            model = rc2.compute()
            return [i for i in range(m) if (i+1) in model]

        # Precompute static max set size
        max_size = max(sizes) if sizes else 1

        # Greedy initial solution to set an upper bound
        banned = 0
        covered = 0
        sol = []
        while covered != full_mask:
            rem = full_mask & ~covered
            best_i = -1
            best_cov = 0
            # choose set that covers most uncovered
            for i in range(m):
                if (banned >> i) & 1:
                    continue
                cov = (coverage[i] & rem).bit_count()
                if cov > best_cov:
                    best_cov = cov
                    best_i = i
            if best_i < 0:
                # Fallback: should not happen as trivial sets cover each object
                break
            sol.append(best_i)
            covered |= coverage[best_i]
            banned |= conflict_adj[best_i]
        ub = len(sol)
        # initial best solution bitmask
        best_mask = 0
        for idx in sol:
            best_mask |= 1 << idx

        # Prepare for branch-and-bound
        full = full_mask
        bit_count = int.bit_count
        ms = max_size
        c_adj = conflict_adj
        covs = coverage
        cbm = covers_by_mask
        maxsize = sys.maxsize
        # Pre-sort covers for each object descending by coverage size
        covers_sorted = [sorted(covers_by[obj], key=lambda i, covs=covs, bit_count=bit_count: -bit_count(covs[i])) for obj in range(n)]

        # Depth-first search with pruning
        def dfs(banned_mask: int, covered_mask: int, sol_mask: int, depth: int):
            nonlocal ub, best_mask
            if covered_mask == full:
                ub = depth
                best_mask = sol_mask
                return
            # Lower bound on additional sets needed
            uncovered = full & ~covered_mask
            uncnt = bit_count(uncovered)
            lb = (uncnt + ms - 1) // ms
            if depth + lb >= ub:
                return
            # Choose uncovered object with fewest available sets
            sel_obj = -1
            min_opts = maxsize
            temp_uncovered = uncovered
            while temp_uncovered:
                lsb = temp_uncovered & -temp_uncovered
                obj = lsb.bit_length() - 1
                temp_uncovered ^= lsb
                avail_mask = cbm[obj] & ~banned_mask
                opts = bit_count(avail_mask)
                if opts == 0:
                    return
                if opts < min_opts:
                    min_opts = opts
                    sel_obj = obj
                    if opts == 1:
                        break
            # Branch on sets covering selected object
            for i in covers_sorted[sel_obj]:
                if (banned_mask >> i) & 1:
                    continue
                dfs(banned_mask | c_adj[i], covered_mask | covs[i], sol_mask | (1 << i), depth + 1)
                if ub <= depth + 1:
                    break

        dfs(0, 0, 0, 0)

        # Reconstruct solution list from best_mask
        result = []
        bm = best_mask
        while bm:
            lsb = bm & -bm
            idx = lsb.bit_length() - 1
            result.append(idx)
            bm ^= lsb
        return result
        return best
EOF
