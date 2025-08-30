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
PROBLEM_SIZE = 555           # Task difficulty (i.e. "n" in AlgoTune)
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
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from scipy.linalg import expm

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs: Any) -> Dict[str, List[List[float]]]:
        """
        Compute the matrix exponential exp(A) for a given square matrix A.

        Fast paths:
          - 1x1: scalar exponential
          - 2x2: closed-form via scaling around trace/2

        Fallback:
          - scipy.linalg.expm for all other cases

        Output is a list of NumPy row arrays to minimize conversion overhead
        while satisfying the validator's requirement that the top-level is a list.
        """
        A_in = problem.get("matrix")
        expm_fn = expm  # local binding for slight speedup

        # Determine shape without forcing array conversion
        if isinstance(A_in, np.ndarray):
            n, m = A_in.shape
        else:
            n = len(A_in)
            m = len(A_in[0]) if n > 0 else 0

        # Non-square fallback to robust SciPy
        if n != m:
            expA = expm_fn(A_in)
            return {"exponential": [expA[i] for i in range(expA.shape[0])]}  # list of row views

        # 1x1 fast path
        if n == 1:
            # Support both ndarray and list-of-lists
            a00 = A_in[0, 0] if isinstance(A_in, np.ndarray) else A_in[0][0]
            val = np.exp(a00)
            return {"exponential": [np.array([val])]}  # list with single 1D row array

        # 2x2 closed-form (works for real/complex)
        if n == 2:
            if isinstance(A_in, np.ndarray):
                a, b = A_in[0, 0], A_in[0, 1]
                c, d = A_in[1, 0], A_in[1, 1]
                is_complex = np.iscomplexobj(A_in)
            else:
                a, b = A_in[0][0], A_in[0][1]
                c, d = A_in[1][0], A_in[1][1]
                is_complex = any(isinstance(x, complex) for x in (a, b, c, d))

            tr = a + d
            a0 = 0.5 * tr
            detA = a * d - b * c
            mu2 = a0 * a0 - detA
            if (not is_complex) and mu2 >= 0:
                mu = float(np.sqrt(mu2))
                if mu < 1e-12:
                    ch = 1.0
                    s_over_mu = 1.0
                else:
                    ch = np.cosh(mu)
                    s_over_mu = np.sinh(mu) / mu
                B00 = a - a0
                B11 = d - a0
                ea = float(np.exp(a0))
                M00 = ea * (ch + s_over_mu * B00)
                M01 = ea * (s_over_mu * b)
                M10 = ea * (s_over_mu * c)
                M11 = ea * (ch + s_over_mu * B11)
                row0 = np.array([M00, M01], dtype=float)
                row1 = np.array([M10, M11], dtype=float)
                return {"exponential": [row0, row1]}
            else:
                mu = np.sqrt(mu2 + 0j)
                if abs(mu) < 1e-12:
                    ch = 1.0 + 0j
                    s_over_mu = 1.0 + 0j
                else:
                    ch = np.cosh(mu)
                    s_over_mu = np.sinh(mu) / mu
                ea = np.exp(a0 + 0j)
                B00 = (a + 0j) - a0
                B11 = (d + 0j) - a0
                M00 = ea * (ch + s_over_mu * B00)
                M01 = ea * (s_over_mu * (b + 0j))
                M10 = ea * (s_over_mu * (c + 0j))
                M11 = ea * (ch + s_over_mu * B11)
                row0 = np.array([M00, M01])
                row1 = np.array([M10, M11])
                # If result is effectively real for real input, drop tiny imag
                if (not is_complex) and (row0.dtype.kind == "c" or row1.dtype.kind == "c"):
                    if max(np.max(np.abs(row0.imag)), np.max(np.abs(row1.imag))) < 1e-12:
                        row0 = row0.real
                        row1 = row1.real
                return {"exponential": [row0, row1]}

        # General fallback
        expA = expm_fn(A_in)
        return {"exponential": [expA[i] for i in range(expA.shape[0])]}
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
