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
PROBLEM_SIZE = 102713           # Task difficulty (i.e. "n" in AlgoTune)
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
from scipy.optimize import least_squares, leastsq
from typing import Any, Callable
import multiprocessing
import time

def _safe_exp(z: np.ndarray | float) -> np.ndarray | float:
    """Exponentiation clipped to avoid overflow."""
    return np.exp(np.clip(z, -50.0, 50.0))

def _run_optimization(residual, guess, bounds, timeout):
    """Run optimization with timeout using multiprocessing."""
    def worker(res, res_queue):
        try:
            result = least_squares(residual, guess, bounds=bounds, max_nfev=5000)
            res_queue.put(result)
        except Exception as e:
            res_queue.put(e)
    
    res_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(residual, res_queue))
    p.start()
    p.join(timeout=timeout)
    
    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError("Optimization timed out")
    
    result = res_queue.get()
    if isinstance(result, Exception):
        raise result
    return result

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        model_type = problem["model_type"]
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        
        if model_type == "polynomial":
            deg = problem["degree"]
            # Create Vandermonde matrix using iterative computation to avoid exponentiation
            n = len(x_data)
            vander = np.empty((n, deg+1))
            vander[:, deg] = 1.0  # x^0
            for i in range(deg-1, -1, -1):
                vander[:, i] = x_data * vander[:, i+1]
            params_opt, _, _, _ = np.linalg.lstsq(vander, y_data, rcond=None)
            return {"params": params_opt.tolist()}
        
        # For nonlinear models, use bounded optimization
        residual, guess, bounds = self._create_residual_function(problem)
        
        try:
            # Try with timeout (90% of allowed time)
            result = _run_optimization(residual, guess, bounds, timeout=9)
            params_opt = result.x
            if np.isnan(params_opt).any():
                raise RuntimeError("Invalid parameters")
            return {"params": params_opt.tolist()}
        except (TimeoutError, RuntimeError, ValueError):
            # Fallback to reference method with increased iteration limit
            residual_ref, guess_ref = self._create_reference_residual(problem)
            params_opt_ref, _, _, _, _ = leastsq(
                residual_ref, guess_ref, full_output=True, maxfev=20000
            )
            return {"params": params_opt_ref.tolist()}
        except:
            # Fallback to reference method
            residual_ref, guess_ref = self._create_reference_residual(problem)
            params_opt_ref, _, _, _, _ = leastsq(
                residual_ref, guess_ref, full_output=True, maxfev=10000
            )
            return {"params": params_opt_ref.tolist()}
    
    def _create_residual_function(
        self, problem: dict[str, Any]
    ) -> tuple[Callable, np.ndarray, tuple]:
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]
        
        if model_type == "exponential":
            def residual(p):
                a, b, c = p
                return y_data - (a * _safe_exp(b * x_data) + c)
            
            guess = np.array([1.0, 0.05, 0.0])
            bounds = ([-np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "logarithmic":
            # Robust initial guess using linear regression on log-transformed data
            x_min = np.min(x_data)
            shift = max(0, -x_min) + 1e-3
            log_x = np.log(x_data + shift)
            slope, intercept = np.polyfit(log_x, y_data, 1)
            
            def residual(p):
                a, b, c, d = p
                # Add small epsilon to avoid log(0)
                return y_data - (a * np.log(b * x_data + c + 1e-12) + d)
            
            guess = np.array([slope, 1.0, shift, intercept])
            # Constrain b and c to be positive
            bounds = ([-np.inf, 1e-12, 1e-12, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "sigmoid":
            def residual(p):
                a, b, c, d = p
                z = -b * (x_data - c)
                return y_data - (a / (1 + _safe_exp(z)) + d)
            
            guess = np.array([3.0, 0.5, np.median(x_data), 0.0])
            # Constrain a, b to be positive
            bounds = ([1e-12, 1e-12, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "sinusoidal":
            # Use grid search for frequency if dataset is small
            n = len(x_data)
            y_mean = np.mean(y_data)
            y_centered = y_data - y_mean
            
            if n > 50:
                # Use FFT for larger datasets
                fft = np.fft.rfft(y_centered)
                freqs = np.fft.rfftfreq(n)
                idx = np.argmax(np.abs(fft[1:])) + 1
                freq = freqs[idx]
                b_guess = 2 * np.pi * freq * n / (np.max(x_data) - np.min(x_data))
            else:
                # Grid search for smaller datasets
                b_candidates = np.linspace(0.1, 10, 20)
                best_score = float('inf')
                for b in b_candidates:
                    # Simple phase estimation
                    phase = np.arctan2(np.sin(b * x_data).dot(y_centered),
                                 np.cos(b * x_data).dot(y_centered))
                    a = np.sqrt(np.mean((y_centered * np.sin(b * x_data + phase))**2 + 
                                (y_centered * np.cos(b * x_data + phase))**2))
                    residuals = y_centered - a * np.sin(b * x_data + phase)
                    score = np.sum(residuals**2)
                    if score < best_score:
                        best_score = score
                        b_guess = b
            
            # Simple phase estimation
            phase = np.arctan2(np.sin(b_guess * x_data).dot(y_centered),
                         np.cos(b_guess * x_data).dot(y_centered))
            a_guess = np.std(y_centered) * np.sqrt(2)
            
            guess = np.array([a_guess, b_guess, phase, y_mean])
            bounds = ([-np.inf, 1e-12, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.sin(b * x_data + c) + d)
            
            return residual, guess, bounds
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_reference_residual(
        self, problem: dict[str, Any]
    ) -> tuple[Callable, np.ndarray]:
        """Create residual function in reference style (without bounds)"""
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]
        
        if model_type == "exponential":
            def residual(p):
                a, b, c = p
                return y_data - (a * _safe_exp(b * x_data) + c)
            guess = np.array([1.0, 0.05, 0.0])
        elif model_type == "logarithmic":
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.log(b * x_data + c + 1e-12) + d)
            guess = np.array([1.0, 1.0, 1.0, 0.0])
        elif model_type == "sigmoid":
            def residual(p):
                a, b, c, d = p
                return y_data - (a / (1 + _safe_exp(-b * (x_data - c))) + d)
            guess = np.array([3.0, 0.5, np.median(x_data), 0.0])
        elif model_type == "sinusoidal":
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.sin(b * x_data + c) + d)
            guess = np.array([2.0, 1.0, 0.0, 0.0])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        return residual, guess
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
