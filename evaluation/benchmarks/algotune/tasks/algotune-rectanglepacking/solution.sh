#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
from ortools.sat.python import cp_model

class Solver:
    """
    A hybrid solver for the Rectangle Packing problem.

    This implementation combines a fast greedy heuristic with the power of the
    CP-SAT solver, using the heuristic's result to set a strong lower bound
    on the objective.

    The solution process is as follows:
    1.  **Greedy Pre-solver**: A fast greedy algorithm is run first to find a
        high-quality initial solution and determine the number of rectangles it
        can place (`greedy_objective_value`).
    2.  **Objective Lower Bound**: This `greedy_objective_value` is then used to
        constrain the CP-SAT model. A constraint `sum(placed) >= greedy_objective_value`
        is added, forcing the solver to only search for solutions that are at
        least as good as the one found by the fast heuristic. This dramatically
        prunes the search space.
    3.  **Efficient Model**: The underlying CP-SAT model is highly efficient,
        using tightly-bounded variables for each orientation and the powerful
        `add_no_overlap_2d` global constraint.
    4.  **Parallelism**: The solver is configured to use multiple workers,
        allowing its robust default search portfolio to run in parallel.
    """
    def solve(self, problem: Any, **kwargs) -> Any:
        W, H = problem[0], problem[1]
        original_rects = problem[2]

        # --- Pre-processing ---
        rects_to_model = []
        for i, r_tuple in enumerate(original_rects):
            w, h, rotatable = r_tuple
            if (w <= W and h <= H) or (rotatable and h <= W and w <= H):
                rects_to_model.append({'w': w, 'h': h, 'r': rotatable, 'idx': i})

        # --- Fast Greedy Heuristic to find a lower bound ---
        greedy_solution_count = 0
        placed_rect_dims = []
        greedy_sorted_rects = sorted(rects_to_model, key=lambda item: max(item['h'], item['w']), reverse=True)
        candidate_points = set([(0, 0)])

        for item in greedy_sorted_rects:
            w, h, r = item['w'], item['h'], item['r']
            best_pos = None
            best_score = (H + 1, W + 1)

            orientations = [(w, h, False)]
            if r and w != h:
                orientations.append((h, w, True))

            for p_x, p_y in sorted(list(candidate_points)):
                for current_w, current_h, is_rotated in orientations:
                    if p_x + current_w > W or p_y + current_h > H:
                        continue

                    is_valid = True
                    for pr_x, pr_y, pr_w, pr_h in placed_rect_dims:
                        if p_x < pr_x + pr_w and p_x + current_w > pr_x and \
                           p_y < pr_y + pr_h and p_y + current_h > pr_y:
                            is_valid = False
                            break
                    
                    if is_valid:
                        score = (p_y, p_x)
                        if score < best_score:
                            best_score = score
                            best_pos = (p_x, p_y, current_w, current_h)
            
            if best_pos:
                x, y, placed_w, placed_h = best_pos
                greedy_solution_count += 1
                placed_rect_dims.append((x, y, placed_w, placed_h))
                candidate_points.add((x + placed_w, y))
                candidate_points.add((x, y + placed_h))

        # --- CP-SAT Model ---
        model_sorted_rects = sorted(rects_to_model, key=lambda item: item['w'] * item['h'], reverse=True)
        model = cp_model.CpModel()
        all_x_intervals, all_y_intervals, all_presences_info, all_presence_vars = [], [], [], []

        for item in model_sorted_rects:
            i, w, h, r = item['idx'], item['w'], item['h'], item['r']
            item_orientations = []
            if w <= W and h <= H:
                pres = model.new_bool_var(f'pres_main_{i}')
                x = model.new_int_var(0, W - w, f'x_main_{i}')
                y = model.new_int_var(0, H - h, f'y_main_{i}')
                all_presences_info.append({'item_idx': i, 'rotated': False, 'var': pres, 'x': x, 'y': y})
                all_x_intervals.append(model.new_optional_fixed_size_interval_var(x, w, pres, f'ix_main_{i}'))
                all_y_intervals.append(model.new_optional_fixed_size_interval_var(y, h, pres, f'iy_main_{i}'))
                item_orientations.append(pres)
                all_presence_vars.append(pres)
            if r and w != h and h <= W and w <= H:
                pres = model.new_bool_var(f'pres_rot_{i}')
                x = model.new_int_var(0, W - h, f'x_rot_{i}')
                y = model.new_int_var(0, H - w, f'y_rot_{i}')
                all_presences_info.append({'item_idx': i, 'rotated': True, 'var': pres, 'x': x, 'y': y})
                all_x_intervals.append(model.new_optional_fixed_size_interval_var(x, h, pres, f'ix_rot_{i}'))
                all_y_intervals.append(model.new_optional_fixed_size_interval_var(y, w, pres, f'iy_rot_{i}'))
                item_orientations.append(pres)
                all_presence_vars.append(pres)
            if len(item_orientations) > 1:
                model.add_at_most_one(item_orientations)

        if all_x_intervals:
            model.add_no_overlap_2d(all_x_intervals, all_y_intervals)
        
        # --- Add Lower Bound and Objective ---
        if greedy_solution_count > 0:
            model.add(sum(all_presence_vars) >= greedy_solution_count)
        model.maximize(sum(all_presence_vars))

        # --- Solve ---
        solver = cp_model.CpSolver()
        time_limit = kwargs.get("time_limit")
        if time_limit is not None:
            solver.parameters.max_time_in_seconds = float(time_limit)
        solver.parameters.num_search_workers = 8

        status = solver.Solve(model)

        # --- Extract Solution ---
        solution = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for p in all_presences_info:
                if solver.value(p['var']):
                    solution.append((p['item_idx'], solver.value(p['x']), solver.value(p['y']), p['rotated']))
        return solution
EOF
