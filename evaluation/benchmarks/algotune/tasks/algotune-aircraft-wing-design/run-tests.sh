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
PROBLEM_SIZE = 10           # Task difficulty (i.e. "n" in AlgoTune)
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
import cvxpy as cp
import numpy as np

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> dict[str, Any]:
        """
        Solve the aircraft wing design optimization problem using CVXPY.
        This implementation uses vectorization to speed up problem construction.
        """
        # Extract problem parameters
        num_conditions = problem["num_conditions"]
        conditions = problem["conditions"]

        # --- Vectorized Parameter Extraction ---
        CDA0 = np.array([c["CDA0"] for c in conditions])
        C_Lmax = np.array([c["C_Lmax"] for c in conditions])
        N_ult = np.array([c["N_ult"] for c in conditions])
        S_wetratio = np.array([c["S_wetratio"] for c in conditions])
        V_min = np.array([c["V_min"] for c in conditions])
        W_0 = np.array([c["W_0"] for c in conditions])
        W_W_coeff1 = np.array([c["W_W_coeff1"] for c in conditions])
        W_W_coeff2 = np.array([c["W_W_coeff2"] for c in conditions])
        e = np.array([c["e"] for c in conditions])
        k = np.array([c["k"] for c in conditions])
        mu = np.array([c["mu"] for c in conditions])
        rho = np.array([c["rho"] for c in conditions])
        tau = np.array([c["tau"] for c in conditions])

        # --- Define shared design variables ---
        A = cp.Variable(pos=True, name="A")  # aspect ratio
        S = cp.Variable(pos=True, name="S")  # wing area (m²)

        # --- Define condition-specific vectorized variables ---
        V = cp.Variable(num_conditions, pos=True, name="V")
        W = cp.Variable(num_conditions, pos=True, name="W")
        Re = cp.Variable(num_conditions, pos=True, name="Re")
        C_D = cp.Variable(num_conditions, pos=True, name="C_D")
        C_L = cp.Variable(num_conditions, pos=True, name="C_L")
        C_f = cp.Variable(num_conditions, pos=True, name="C_f")
        W_w = cp.Variable(num_conditions, pos=True, name="W_w")

        # --- Define constraints in vectorized form ---
        constraints = []

        # Drag coefficient model: C_D >= CDA0/S + k*C_f*S_wetratio + C_L^2/(pi*A*e)
        term1_cd = CDA0 * cp.inv_pos(S)
        term2_cd = cp.multiply(k * S_wetratio, C_f)
        term3_cd = cp.multiply(1 / (np.pi * e), cp.power(C_L, 2)) * cp.inv_pos(A)
        constraints.append(C_D >= term1_cd + term2_cd + term3_cd)

        # Skin friction model: C_f >= 0.074 / Re^0.2
        constraints.append(C_f >= 0.074 * cp.power(Re, -0.2))

        # Reynolds number definition: Re * mu >= rho * V * sqrt(S/A)
        constraints.append(
            cp.multiply(Re, mu) >= cp.multiply(rho, V) * cp.sqrt(S * cp.inv_pos(A))
        )

        # Wing weight model: W_w >= W_W_coeff2*S + W_W_coeff1*N_ult*A^(1.5)*sqrt(W_0*W)/tau
        term1_ww = W_W_coeff2 * S
        c_ww = (W_W_coeff1 * N_ult) / tau
        term2_ww = cp.multiply(c_ww * cp.power(A, 1.5), cp.sqrt(cp.multiply(W_0, W)))
        constraints.append(W_w >= term1_ww + term2_ww)

        # Total weight: W >= W_0 + W_w
        constraints.append(W >= W_0 + W_w)

        # Lift equals weight: W <= 0.5 * rho * V^2 * C_L * S
        constraints.append(
            W <= 0.5 * S * cp.multiply(rho, cp.multiply(cp.power(V, 2), C_L))
        )

        # Stall constraint: 2*W/(rho * V_min^2 * S) <= C_Lmax
        c_stall = 2 / (rho * V_min**2)
        constraints.append(cp.multiply(c_stall, W) * cp.inv_pos(S) <= C_Lmax)

        # --- Define the objective ---
        # Minimize average drag: (1/n) * sum(0.5 * rho * V^2 * C_D * S)
        drag_vec = 0.5 * S * cp.multiply(rho, cp.multiply(cp.power(V, 2), C_D))
        objective = cp.Minimize(cp.sum(drag_vec) / num_conditions)

        # --- Solve the problem ---
        prob = cp.Problem(objective, constraints)
        try:
            prob.solve(gp=True, solver=cp.ECOS, warm_start=True, feastol=1e-5, abstol=1e-4, reltol=1e-4)

            if prob.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE} or A.value is None:
                return {"A": [], "S": [], "avg_drag": 0.0, "condition_results": []}

            # --- Collect results ---
            condition_results = []
            drag_values = 0.5 * S.value * rho * (V.value**2) * C_D.value
            for i in range(num_conditions):
                condition_results.append(
                    {
                        "condition_id": conditions[i]["condition_id"],
                        "V": float(V.value[i]),
                        "W": float(W.value[i]),
                        "W_w": float(W_w.value[i]),
                        "C_L": float(C_L.value[i]),
                        "C_D": float(C_D.value[i]),
                        "C_f": float(C_f.value[i]),
                        "Re": float(Re.value[i]),
                        "drag": float(drag_values[i]),
                    }
                )

            return {
                "A": float(A.value),
                "S": float(S.value),
                "avg_drag": float(prob.value),
                "condition_results": condition_results,
            }

        except (cp.SolverError, Exception):
            return {"A": [], "S": [], "avg_drag": 0.0, "condition_results": []}
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
