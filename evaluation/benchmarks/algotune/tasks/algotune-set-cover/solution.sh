#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from __future__ import annotations

from typing import Any, List, Tuple

class Solver:
    def solve(self, problem: List[List[int]], **kwargs) -> Any:
        """
        Solve the Set Cover problem optimally.

        Input: problem is a list of lists (subsets) with elements labeled 1..n (n = max element).
        Output: list of 1-indexed indices of selected subsets that form an optimal cover.

        Strategy:
        - Convert to bitmasks for fast ops.
        - Deduplicate identical sets (keep earliest index).
        - Eliminate dominated sets (remove any set that is a subset of another).
        - Force-pick sets for elements with unique coverage.
        - Use greedy to get an initial upper bound.
        - Branch-and-bound with heuristic branching and lower bounds using bit operations.
        """
        # Edge cases
        if not problem:
            return []

        # Build universe (1..n) and basic data
        max_elem = 0
        for s in problem:
            if s:
                me = max(s)
                if me > max_elem:
                    max_elem = me
        if max_elem == 0:
            return []

        # Convert subsets to bitmasks; deduplicate keeping earliest index
        mask_to_idx: dict[int, int] = {}
        masks: List[int] = []
        orig_indices: List[int] = []  # store 1-based index mapped from original problem

        for idx0, subset in enumerate(problem):
            m = 0
            for e in subset:
                if 1 <= e <= max_elem:
                    m |= 1 << (e - 1)
            if m == 0:
                continue  # empty set never helps for non-empty universe
            if m not in mask_to_idx:
                mask_to_idx[m] = idx0 + 1  # 1-based
                masks.append(m)
                orig_indices.append(idx0 + 1)
            else:
                # keep the earliest index deterministically (already stored)
                pass

        if not masks:
            # If there is no non-empty set but universe might be non-empty, no feasible solution
            return []

        # Universe as OR of all masks
        U = 0
        for m in masks:
            U |= m
        if U == 0:
            return []

        # Eliminate dominated sets: remove any set that is a subset of another (unit costs).
        # Sort by popcount descending; keep a set only if it's not subset of an already kept set.
        order = sorted(range(len(masks)), key=lambda i: masks[i].bit_count(), reverse=True)
        kept_masks: List[int] = []
        kept_indices: List[int] = []
        for i in order:
            m = masks[i]
            # Check if m is subset of any kept mask
            is_subset = False
            for km in kept_masks:
                if (m & km) == m:
                    is_subset = True
                    break
            if not is_subset:
                kept_masks.append(m)
                kept_indices.append(orig_indices[i])

        masks = kept_masks
        orig_indices = kept_indices

        # Recompute universe
        U = 0
        for m in masks:
            U |= m

        # If for some reason universe changed (shouldn't), handle gracefully
        if U == 0:
            return []

        # Build cover lists for each element (0-based bit index)
        n = max_elem
        cover_lists: List[List[int]] = [[] for _ in range(n)]
        for si, m in enumerate(masks):
            mm = m
            while mm:
                b = mm & -mm
                e = (b.bit_length() - 1)  # 0-based
                cover_lists[e].append(si)
                mm ^= b

        # Forced selections: elements with unique covering set must include that set.
        selected_internal: List[int] = []
        selected_mask = 0

        while True:
            changed = False
            # Find elements in current uncovered U that have exactly one covering set
            rem = U & ~selected_mask
            if rem == 0:
                break
            mm = rem
            unique_sets_to_add = set()
            while mm:
                b = mm & -mm
                e = b.bit_length() - 1
                # count sets that cover e
                cl = cover_lists[e]
                if not cl:
                    # No set covers this element: instance malformed; but return empty (no solution)
                    return []
                if len(cl) == 1:
                    unique_sets_to_add.add(cl[0])
                mm ^= b
            if unique_sets_to_add:
                for si in unique_sets_to_add:
                    if (selected_mask & masks[si]) != masks[si]:
                        # add this set
                        selected_internal.append(si)
                        selected_mask |= masks[si]
                        changed = True
                # continue loop to propagate more forced picks
            if not changed:
                break

        # If everything covered by forced picks, return
        if (U & ~selected_mask) == 0:
            res = sorted({orig_indices[si] for si in selected_internal})
            return res

        # Prepare greedy upper bound to prune
        # Quick check: if any single set covers the remaining elements, return it immediately.
        rem0 = U & ~selected_mask
        for si, m in enumerate(masks):
            if (m & rem0) == rem0:
                res = sorted({orig_indices[si]} | {orig_indices[s] for s in selected_internal})
                return res

        def greedy_cover(start_mask: int) -> Tuple[int, List[int]]:
            rem = start_mask
            picks: List[int] = []
            # Using a simple heuristic: pick the set with the largest coverage of remaining
            while rem:
                best_si = -1
                best_cover = 0
                for si, m in enumerate(masks):
                    cov = (m & rem).bit_count()
                    if cov > best_cover:
                        best_cover = cov
                        best_si = si
                if best_si == -1 or best_cover == 0:
                    # no progress, infeasible
                    return (10**9, [])
                picks.append(best_si)
                rem &= ~masks[best_si]
            return (len(picks), picks)

        # Initial upper bound: forced picks + greedy for the rest
        greedy_len, greedy_picks = greedy_cover(rem0)
        if greedy_len >= 10**9:
            # Should not happen if instance well-formed
            return []
        best_len = len(selected_internal) + greedy_len
        best_solution_internal = selected_internal + greedy_picks

        # Precompute element difficulty (number of covering sets) for heuristic branching
        elem_cover_counts = [len(cover_lists[e]) for e in range(n)]

        # Cache: memoize the best number of picks seen for a remainder mask to prune
        # cache[rem_mask] = minimal number of additional sets used so far to reach this state
        cache: dict[int, int] = {}

        # Precompute a quick global bound denominator: maximum set size overall
        if masks:
            max_static_size = max(m.bit_count() for m in masks)
        else:
            max_static_size = 1

        # Lower bound function: ceil(remaining_elements / max_cover_per_set)
        # Two-stage: quick bound using max_static_size; if not pruning, compute dynamic bound.
        def lower_bound(rem: int, picks_len: int, best_len_local: int) -> int:
            if rem == 0:
                return 0
            rcount = rem.bit_count()
            # Quick bound
            lb_quick = (rcount + max_static_size - 1) // max_static_size
            if picks_len + lb_quick >= best_len_local:
                return lb_quick  # sufficient for pruning
            # Dynamic bound
            if rcount <= 1:
                return 1
            max_cov = 0
            # Scan sets for max coverage on rem; early exit if equals rcount
            for m in masks:
                c = (m & rem).bit_count()
                if c > max_cov:
                    max_cov = c
                    if max_cov >= rcount:
                        return 1
            if max_cov == 0:
                return 10**9
            return (rcount + max_cov - 1) // max_cov

        # Choose the most constrained element (fewest covering sets) among rem bits
        def choose_element(rem: int) -> int:
            # Return 0-based bit index of chosen element
            mm = rem
            best_e = -1
            best_deg = 10**9
            while mm:
                b = mm & -mm
                e = b.bit_length() - 1
                deg = elem_cover_counts[e]
                if deg < best_deg:
                    best_deg = deg
                    best_e = e
                    if best_deg <= 1:
                        break
                mm ^= b
            return best_e

        # Depth-first search with pruning
        def dfs(rem: int, picks: List[int]) -> None:
            nonlocal best_len, best_solution_internal

            # Covered?
            if rem == 0:
                if len(picks) < best_len:
                    best_len = len(picks)
                    best_solution_internal = picks.copy()
                return

            # Prune by bound
            lb = lower_bound(rem, len(picks), best_len)
            if len(picks) + lb >= best_len:
                return

            # Transposition table prune
            prev = cache.get(rem)
            if prev is not None and len(picks) >= prev:
                return
            cache[rem] = len(picks)

            # Branch on most constrained element
            e = choose_element(rem)
            if e < 0:
                # Shouldn't happen
                return
            candidates = cover_lists[e]
            # Build candidate list with coverage masks and sizes on rem
            cand: List[Tuple[int, int, int]] = []
            for si in candidates:
                cm = masks[si] & rem
                cov = cm.bit_count()
                if cov > 0:
                    cand.append((si, cm, cov))
            if not cand:
                # No set covers this element -> infeasible
                return

            # Order candidates by coverage size on rem descending (fail-first good solutions)
            cand.sort(key=lambda t: t[2], reverse=True)

            # Optional dominance among candidates: remove those whose coverage is subset of another
            filtered: List[Tuple[int, int]] = []
            cov_masks: List[int] = []
            for si, cm, _ in cand:
                dominated = False
                for om in cov_masks:
                    # If cm subset of om, skip this candidate
                    if (cm & om) == cm:
                        dominated = True
                        break
                if not dominated:
                    filtered.append((si, cm))
                    cov_masks.append(cm)

            for si, cm in filtered:
                # Choose si
                npicks_len = len(picks) + 1
                if npicks_len >= best_len:
                    continue
                new_rem = rem & ~cm  # cm == masks[si] & rem
                picks.append(si)
                dfs(new_rem, picks)
                picks.pop()

        # Start DFS from remaining part; picks already include forced selections
        base_picks = selected_internal.copy()
        dfs(U & ~selected_mask, base_picks)

        # Compose final solution from internal indices -> original 1-based indices
        res_set = {orig_indices[si] for si in best_solution_internal}
        # Ensure forced selections are included (they already are)
        res = sorted(res_set)
        return res
EOF
