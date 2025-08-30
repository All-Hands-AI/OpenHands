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
PROBLEM_SIZE = 24921           # Task difficulty (i.e. "n" in AlgoTune)
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
import numpy as np
from scipy import signal
import numba
from numba import jit, float64

@jit(nopython=True, fastmath=True)
def taylor_expm(M, max_terms=15):
    """Compute matrix exponential using Taylor series approximation."""
    n = M.shape[0]
    expM = np.eye(n)
    term = np.eye(n)
    for k in range(1, max_terms+1):
        term = term @ M / k
        expM += term
    return expM

class Solver:
    def __init__(self):
        self.cache = {}
    
    def solve(self, problem: dict) -> dict:
        num = problem["num"]
        den = problem["den"]
        u = problem["u"]
        t = problem["t"]
        
        # Convert to state-space
        A, B, C, D = signal.tf2ss(num, den)
        n = A.shape[0]
        
        # Handle static systems
        if n == 0:
            return {"yout": [float(D * val) for val in u]}
        
        # Precompute constant matrices
        B = B.flatten()
        C = C.flatten()
        D = D.item() if D.size == 1 else D
        
        # Initialize output array
        yout = np.zeros(len(t))
        yout[0] = D * u[0]
        
        # Compute time steps
        dts = np.diff(t)
        constant_dt = len(dts) > 0 and np.all(np.abs(dts - dts[0]) < 1e-10)
        
        # Precompute matrices
        if constant_dt:
            # Single dt for all steps
            dt = dts[0]
            if dt > 1e-8:
                cache_key = (dt, tuple(A.ravel()), tuple(B))
                if cache_key not in self.cache:
                    M = np.zeros((n+2, n+2))
                    M[:n, :n] = A * dt
                    M[:n, n] = B * dt
                    M[:n, n+1] = np.zeros(n)
                    M[n, n+1] = 1
                    expM = taylor_expm(M)
                    F = expM[:n, :n]
                    G1 = expM[:n, n]
                    G2 = expM[:n, n+1]
                    self.cache[cache_key] = (F, G1, G2)
                
                F_val, G1_val, G2_val = self.cache[cache_key]
                F_arr = np.tile(F_val, (len(dts), 1, 1))
                G1_arr = np.tile(G1_val, (len(dts), 1))
                G2_arr = np.tile(G2_val, (len(dts), 1))
            else:
                F_arr = np.tile(np.eye(n), (len(dts), 1, 1))
                G1_arr = np.zeros((len(dts), n))
                G2_arr = np.zeros((len(dts), n))
        else:
            # Variable time steps
            F_arr = np.zeros((len(dts), n, n))
            G1_arr = np.zeros((len(dts), n))
            G2_arr = np.zeros((len(dts), n))
            
            # Precompute for each dt value
            for i, dt in enumerate(dts):
                if dt > 1e-8:
                    cache_key = (dt, tuple(A.ravel()), tuple(B))
                    if cache_key not in self.cache:
                        M = np.zeros((n+2, n+2))
                        M[:n, :n] = A * dt
                        M[:n, n] = B * dt
                        M[:n, n+1] = np.zeros(n)
                        M[n, n+1] = 1
                        expM = taylor_expm(M)
                        F = expM[:n, :n]
                        G1 = expM[:n, n]
                        G2 = expM[:n, n+1]
                        self.cache[cache_key] = (F, G1, G2)
                    
                    F_arr[i], G1_arr[i], G2_arr[i] = self.cache[cache_key]
                else:
                    F_arr[i] = np.eye(n)
                    G1_arr[i] = np.zeros(n)
                    G2_arr[i] = np.zeros(n)
        
        # Run optimized simulation
        x = np.zeros(n)
        u_arr = np.asarray(u)
        yout = self.numba_simulate(F_arr, G1_arr, G2_arr, u_arr, C, D, n, yout, len(dts))
        
        return {"yout": yout.tolist()}
    
    @staticmethod
    @jit(nopython=True, fastmath=True, boundscheck=False)
    def numba_simulate(F_arr, G1_arr, G2_arr, u, C, D, n, yout, num_steps):
        x = np.zeros(n)
        D_val = D
        C_vec = C
        
        # Handle scalar systems
        if n == 1:
            for i in range(num_steps):
                F = F_arr[i,0,0]
                G1 = G1_arr[i,0]
                G2 = G2_arr[i,0]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F*x[0] + G1*u0 + G2*du
                x[0] = x0
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0
            return yout
        
        # Specialized loops for common system orders
        if n == 2:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + G1[1]*u0 + G2[1]*du
                x[0], x[1] = x0, x1
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1
        elif n == 3:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + F[0,2]*x[2] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + F[1,2]*x[2] + G1[1]*u0 + G2[1]*du
                x2 = F[2,0]*x[0] + F[2,1]*x[1] + F[2,2]*x[2] + G1[2]*u0 + G2[2]*du
                x[0], x[1], x[2] = x0, x1, x2
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1 + C_vec[2]*x2
        elif n == 4:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + F[0,2]*x[2] + F[0,3]*x[3] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + F[1,2]*x[2] + F[1,3]*x[3] + G1[1]*u0 + G2[1]*du
                x2 = F[2,0]*x[0] + F[2,1]*x[1] + F[2,2]*x[2] + F[2,3]*x[3] + G1[2]*u0 + G2[2]*du
                x3 = F[3,0]*x[0] + F[3,1]*x[1] + F[3,2]*x[2] + F[3,3]*x[3] + G1[3]*u0 + G2[3]*du
                x[0], x[1], x[2], x[3] = x0, x1, x2, x3
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1 + C_vec[2]*x2 + C_vec[3]*x3
        else:
            # General case for higher-order systems
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                new_x = np.zeros(n)
                for j in range(n):
                    temp = 0.0
                    for k in range(n):
                        temp += F[j, k] * x[k]
                    new_x[j] = temp + G1[j]*u0 + G2[j]*du
                x = new_x
                
                # Output calculation
                output_val = D_val * u1
                for j in range(n):
                    output_val += C_vec[j] * x[j]
                yout[i+1] = output_val
        
        return yout
EOF

# --- Step 4: Run performance test on the new solver ---
# Execute pytest and parse the output to find the "Calculated Speedup".
# The result is saved to a file. If the test fails or the speedup
# cannot be determined, it defaults to "1.0".
echo "Running performance test..."
(set -o pipefail; pytest -s /workspace/test_outputs.py 2>&1 | tee /workspace/test_outputs.log | tee /dev/stderr | grep "Calculated Speedup" | awk '{print $3}' | sed 's/x$//' > /workspace/.best_solver_speedup.txt) \
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
