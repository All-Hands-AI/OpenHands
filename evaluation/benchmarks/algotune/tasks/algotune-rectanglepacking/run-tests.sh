#!/bin/bash

# This script is designed to first test a candidate "best" solver for performance,
# record its speedup, and then run a final validation test using the original solver.

# --- Step 1: Create the test file ---
# This file contains the tests that will be run against the solvers.
# It's created first to be available for both test runs.
cat > /workspace/test_outputs.py << 'EOF'
# test_outputs.py
import importlib.util
import logging
import time
from pathlib import Path
from typing import Callable, Any, List, Tuple, Union
import numpy as np
import pytest

# --- Configuration ---
SOLVER_PATH = Path("/workspace/solver.py")
BEST_SOLVER_SPEEDUP_FILE = Path('/workspace/.best_solver_speedup.txt')

# --- Problem Generation and Dynamic Measurement Parameters ---
PROBLEM_SIZE = 8           # Task difficulty (i.e. "n" in AlgoTune)
MAX_SAMPLES = 200            # Maximum number of problems to test
MIN_SAMPLES = 30             # Minimum samples before first stability check
STABILITY_BATCH_SIZE = 10    # Check for stability every N new samples
STABILITY_THRESHOLD = 0.01   # Stop when median changes by less than 1%
IQR_STABILITY_THRESHOLD = 0.05 # Stop when IQR changes by less than 5%

# --- Setup ---
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from evaluator import Task
task = Task()


@pytest.fixture(scope="module")
def solver_instance() -> Any:
    """Loads the user's 'Solver' class from solver.py."""
    if not SOLVER_PATH.exists():
        pytest.fail(f"Solver file not found at {SOLVER_PATH}")
    
    spec = importlib.util.spec_from_file_location("solver", SOLVER_PATH)
    solver_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solver_module)
    return solver_module.Solver()

@pytest.fixture(scope="module")
def problem_set() -> List[Any]:
    """Generates a fixed, reproducible set of up to MAX_SAMPLES problems."""
    logger.info(f"Generating {MAX_SAMPLES} unique problems for performance testing...")
    problems = []
    for i in range(MAX_SAMPLES):
        # Use the index 'i' as the seed for reproducibility.
        problem = task.generate_problem(n=PROBLEM_SIZE, random_seed=i)
        problems.append(problem)
    return problems

def _measure_stable_median_time(solve_func: Callable[[Any], Any], problems: List[Any]) -> Tuple[Union[float, str], int]:
    """
    Measures the median execution time, adding samples until both the median
    and the Interquartile Range (IQR) of the timings stabilize.
    """
    measured_times = []
    old_median = 0.0
    old_iqr = 0.0

    for i, problem in enumerate(problems):
        start = time.perf_counter_ns()
        solution = solve_func(problem)
        end = time.perf_counter_ns()

        if not task.is_solution(problem, solution):
            return "Solver produced an invalid solution.", i + 1

        measured_times.append(end - start)

        num_samples = i + 1
        if num_samples >= MIN_SAMPLES and (num_samples - MIN_SAMPLES) % STABILITY_BATCH_SIZE == 0:
            # Calculate current median and IQR
            current_median = np.median(measured_times)
            q75, q25 = np.percentile(measured_times, [75, 25])
            current_iqr = q75 - q25

            # Check for stability only if we have previous values to compare against
            if old_median > 0 and old_iqr > 0:
                relative_median_change = abs(current_median - old_median) / old_median
                # Handle case where IQR is zero to avoid division by zero
                relative_iqr_change = abs(current_iqr - old_iqr) / old_iqr if old_iqr > 0 else 0

                # The new, more robust stability condition
                median_is_stable = relative_median_change < STABILITY_THRESHOLD
                iqr_is_stable = relative_iqr_change < IQR_STABILITY_THRESHOLD
                
                if median_is_stable and iqr_is_stable:
                    logger.info(
                        f"Measurements stabilized after {num_samples} samples. "
                        f"(Median change < {STABILITY_THRESHOLD*100:.1f}%, "
                        f"IQR change < {IQR_STABILITY_THRESHOLD*100:.1f}%)"
                    )
                    return current_median, num_samples
            
            old_median = current_median
            old_iqr = current_iqr

    # Fallback if stability wasn't reached by MAX_SAMPLES
    final_median = np.median(measured_times) if measured_times else 0
    logger.warning(f"Measurements did not stabilize. Reporting result from all {len(measured_times)} samples.")
    return final_median, len(measured_times)

@pytest.fixture(scope="module")
def performance_results(solver_instance, problem_set) -> dict:
    """
    Calculates performance by running the solver and baseline until timing stabilizes.
    """
    logger.info("Calculating performance with dynamic sampling...")

    # Measure time for the user's solver dynamically
    median_solver_time, solver_samples = _measure_stable_median_time(
        solver_instance.solve,
        problems=problem_set
    )
    
    # Measure time for the baseline dynamically on the exact same problem set
    median_baseline_time, baseline_samples = _measure_stable_median_time(
        task.solve,
        problems=problem_set
    )

    if isinstance(median_solver_time, str):
        validity = median_solver_time
        median_solver_time = 0.0
        median_baseline_time = 0.0
        speedup = 0.0
    else:
        validity = True
        speedup = median_baseline_time / median_solver_time if median_solver_time > 0 else float('inf')

    print(f"\n--- Performance Summary ---")
    print(f"Validity: {validity}")
    print(f"Baseline Median Time: {median_baseline_time / 1e9:.4f}s (over {baseline_samples} samples)")
    print(f"Solver Median Time:   {median_solver_time / 1e9:.4f}s (over {solver_samples} samples)")
    print(f"Calculated Speedup:   {speedup:.2f} x")
    print("Keep improving your result!")
    print(f"---------------------------")
    
    return {"speedup": speedup, "validity": validity}


def test_solver_exists():
    """Checks if the solver.py file exists."""
    assert SOLVER_PATH.is_file(), f"Solver file not found at {SOLVER_PATH}"

def test_solver_is_solution(performance_results):
    assert performance_results['validity'] == True, performance_results['validity']

def test_solver_is_faster_than_baseline(performance_results):
    """
    Checks if the solver is at least as fast as the baseline.
    """
    speedup = performance_results["speedup"]
    assert speedup >= 0.9   # A tolerance margin


def test_solver_meets_target_speedup(performance_results):
    """Checks if the solver meets the speedup target from the best submission."""
    if not BEST_SOLVER_SPEEDUP_FILE.exists():
        pytest.skip(f"No best speedup file found at {BEST_SOLVER_SPEEDUP_FILE}. Skipping target test.")
    
    try:
        target_speedup = float(BEST_SOLVER_SPEEDUP_FILE.read_text(encoding='utf-8').strip())
    except (ValueError, FileNotFoundError):
        pytest.skip("Could not read target speedup. Skipping target test.")

    speedup = performance_results["speedup"]
    assert speedup >= target_speedup * 0.9  # A tolerance margin


# For agent to use 
if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
EOF

# --- Step 2: Backup the original solver ---
# Copy the existing solver.py to a backup location before overwriting it.
# This preserves the original code for the final test run.
echo "Backing up original solver..."
cp /workspace/solver.py /workspace/solver.py.bak

# --- Step 3: Write the new "best" solver ---
# The new solver code is written to /workspace/solver.py. This file will be
# used for the performance evaluation in the next step.
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

# --- Step 4: Run performance test on the new solver ---
# Execute pytest and parse the output to find the "Calculated Speedup".
# The result is saved to a file. If the test fails or the speedup
# cannot be determined, it defaults to "1.0".
echo "Running performance test..."
(set -o pipefail; /usr/local/bin/pytest -s /workspace/test_outputs.py 2>&1 | tee /workspace/test_outputs.log | tee /dev/stderr | grep "Calculated Speedup" | awk '{print $3}' | sed 's/x$//' > /workspace/.best_solver_speedup.txt) \
|| echo "1.0" > /workspace/.best_solver_speedup.txt

# --- Output Speedup and Solver Code for Review ---
echo "--- TARGET SPEEDUP ---"
cat /workspace/.best_solver_speedup.txt
echo "--- TARGET SPEED END ---"

# --- Step 5: Restore the original solver ---
# Move the backup file back to /workspace/solver.py, overwriting the
# temporary "best" solver.
echo "Restoring original solver..."
rm -rf /workspace/solver.py
mv /workspace/solver.py.bak /workspace/solver.py

# --- Step 6: Run final tests on the original solver ---
# Now that the original solver is restored, run the final pytest
# validation to ensure correctness.
echo "Running final validation on original solver..."
/usr/local/bin/pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
