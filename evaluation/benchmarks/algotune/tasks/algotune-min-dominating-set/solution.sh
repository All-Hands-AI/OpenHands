#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import List, Any

class Solver:
    """
    Exact branch-and-bound solver for the Minimum Dominating Set problem.
    Uses bitmask representations, dominated-candidate reduction, greedy initial
    solution and pruning with a simple lower bound and memoization.
    """

    def solve(self, problem: List[List[int]], **kwargs) -> Any:
        n = len(problem)
        if n == 0:
            return []

        # Build closed-neighborhood masks Nmask[i] = bitmask of {i} union neighbors(i)
        Nmask = [0] * n
        for i in range(n):
            mask = 1 << i
            row = problem[i]
            for j, val in enumerate(row):
                if val:
                    mask |= 1 << j
            Nmask[i] = mask

        all_mask = (1 << n) - 1

        # Remove dominated candidate vertices: if Nmask[i] is subset of Nmask[j] (i != j),
        # then i is never needed as a dominator (j is at least as powerful).
        keep = [True] * n
        for i in range(n):
            if not keep[i]:
                continue
            mi = Nmask[i]
            for j in range(n):
                if i == j or not keep[j]:
                    continue
                mj = Nmask[j]
                if (mi | mj) == mj:
                    keep[i] = False
                    break

        dominators = [i for i in range(n) if keep[i]]
        if not dominators:
            dominators = list(range(n))

        # Precompute candidate dominators for each vertex u:
        candidate_dominators = [[] for _ in range(n)]
        for u in range(n):
            for v in dominators:
                if (Nmask[v] >> u) & 1:
                    candidate_dominators[u].append(v)

        # popcount helper (fast on modern Python)
        if hasattr(int, "bit_count"):
            popcount = lambda x: x.bit_count()
        else:
            popcount = lambda x: bin(x).count("1")

        # Greedy initial solution (upper bound)
        dom = 0
        greedy_sel: List[int] = []
        while dom != all_mask:
            best_v = -1
            best_gain = -1
            for v in dominators:
                gain = popcount(Nmask[v] & ~dom)
                if gain > best_gain:
                    best_gain = gain
                    best_v = v
            if best_gain <= 0:
                break
            greedy_sel.append(best_v)
            dom |= Nmask[best_v]

        best_size = len(greedy_sel) if greedy_sel else n
        best_solution = greedy_sel.copy() if greedy_sel else list(range(n))

        # Memoization: best known count for a dominated-mask
        visited = {}

        # Precompute candidate lengths for quick access
        cand_len = [len(candidate_dominators[u]) for u in range(n)]

        # Depth-first search with pruning
        def dfs(dom_mask: int, count: int, cur_sel: List[int]):
            nonlocal best_size, best_solution

            if count >= best_size:
                return

            if dom_mask == all_mask:
                best_size = count
                best_solution = cur_sel.copy()
                return

            prev = visited.get(dom_mask)
            if prev is not None and prev <= count:
                return
            visited[dom_mask] = count

            rem_mask = all_mask & ~dom_mask
            rem = popcount(rem_mask)

            # Compute simple lower bound: remaining nodes / best possible coverage
            best_cover = 0
            for v in dominators:
                c = popcount(Nmask[v] & rem_mask)
                if c > best_cover:
                    best_cover = c
            if best_cover == 0:
                return
            lb = (rem + best_cover - 1) // best_cover
            if count + lb >= best_size:
                return

            # Choose an undominated vertex u with smallest number of candidates (least branching)
            best_u = -1
            best_candidates = 10 ** 9
            for u in range(n):
                if ((rem_mask >> u) & 1) == 0:
                    continue
                l = cand_len[u]
                if l < best_candidates:
                    best_candidates = l
                    best_u = u
                    if l <= 2:
                        break

            if best_u == -1:
                return

            # Candidate dominators for best_u, order by coverage (descending) to find good solutions early
            cand = candidate_dominators[best_u]
            cand_sorted = sorted(cand, key=lambda v: -popcount(Nmask[v] & rem_mask))

            for v in cand_sorted:
                new_mask = dom_mask | Nmask[v]
                cur_sel.append(v)
                dfs(new_mask, count + 1, cur_sel)
                cur_sel.pop()
                if count + 1 >= best_size:
                    break

        dfs(0, 0, [])

        # Final safety: ensure result dominates all vertices; otherwise fallback to greedy
        final = sorted(set(best_solution))
        mask_check = 0
        for v in final:
            mask_check |= Nmask[v]
        if mask_check != all_mask:
            final = sorted(set(greedy_sel))

        return final
EOF
