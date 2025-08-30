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
PROBLEM_SIZE = 132           # Task difficulty (i.e. "n" in AlgoTune)
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
# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
import numbers
import sympy



class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the IntegerFactorization task.

        In this task, you are given a composite number that is a product of two large prime numbers.
        The task is to find these two prime factors.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, int]:
        """
        Generate a composite number that is a product of two prime numbers.

        :param n: Parameter controlling the size of the problem. Each prime will be 8*max(1,n) bits long.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary with key "composite" representing the product of two n-bit primes.
        """
        logging.debug(
            f"Generating integer factorization problem with n={n} and random_seed={random_seed}"
        )
        rng = random.Random(random_seed)

        # Calculate the actual bit length for each prime
        n_bits = 8 * max(1, n)

        # Generate two different primes with the calculated bit length
        p = sympy.nextprime(rng.randint(2 ** (n_bits - 1), 2**n_bits - 1))
        q = sympy.nextprime(p)

        # Compute the composite number
        composite = p * q

        logging.debug(
            f"Generated integer factorization problem with composite={composite} "
            f"(primes of {n_bits} bits each)"
        )
        return {"composite": composite}

    def solve(self, problem: dict[str, int]) -> dict[str, int]:
        """
        Solve the integer factorization problem by finding the prime factors of the composite number.

        For a proper solution, one would need to implement a factorization algorithm like:
        - Trial division
        - Pollard's rho algorithm
        - Quadratic sieve
        - General number field sieve

        In this reference implementation, we use sympy's factorization capabilities.

        :param problem: A dictionary containing the composite number.
        :return: A dictionary with keys "p" and "q" containing the two prime factors, where p < q.
        :raises ValueError: If the factorization does not result in exactly two prime factors.
        """
        composite_val = problem["composite"]

        # Ensure composite_val is a SymPy Integer before passing to factorint
        try:
            composite = sympy.Integer(composite_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"The composite value '{composite_val}' could not be converted to a SymPy Integer: {e}")

        # Extract the prime factors using sympy's factorization
        factors = [prime for prime, exp in sympy.factorint(composite).items() for _ in range(exp)]

        # Ensure we have exactly two factors (should always be the case for our generated problems)
        if len(factors) != 2:
            raise ValueError(f"Expected 2 factors, but got {len(factors)}.")

        # Sort the factors to ensure p < q
        p, q = sorted(factors)

        return {"p": p, "q": q}

    def is_solution(self, problem: dict[str, int], solution: dict[str, int]) -> bool:
        """
        Validate factorization:
        - solution is a dict with 'p' and 'q'
        - p*q == composite
        - p and q are prime
        - order is not enforced (we normalize)
        Accepts int-like types (sympy.Integer, numpy.integer) and integer-valued floats/strings.
        """

        def _to_int_like(x, name: str):
            # Allow exact int types, SymPy/Numpy integers
            if isinstance(x, numbers.Integral):
                return int(x)
            # Allow integer-valued floats (e.g., 7.0) — strict about exact integrality
            if isinstance(x, float):
                if x.is_integer():
                    return int(x)
                logging.error(f"{name} is a non-integer float: {x}")
                raise TypeError
            # Allow strings that are pure integers (no spaces/sign is okay)
            if isinstance(x, str):
                s = x.strip()
                if s.startswith(("+", "-")):
                    sign = -1 if s[0] == "-" else 1
                    s_num = s[1:]
                else:
                    sign = 1
                    s_num = s
                if s_num.isdigit():
                    return sign * int(s_num)
                logging.error(f"{name} is a non-integer string: {x!r}")
                raise TypeError
            # Last resort: try int() but be strict (reject 7.2, etc.)
            try:
                xi = int(x)
                # guard against silent truncation (e.g., Decimal('7.2') -> 7)
                if hasattr(x, "__int__") and not isinstance(x, bool):
                    # If it was a float-like, ensure exact equality after cast
                    if isinstance(x, numbers.Real) and float(x) != float(xi):
                        logging.error(f"{name} lost precision converting to int: {x} -> {xi}")
                        raise TypeError
                return xi
            except Exception:
                logging.error(f"{name} cannot be interpreted as an integer (type {type(x)}).")
                raise

        composite = problem.get("composite")
        if composite is None:
            logging.error("Problem does not contain 'composite'.")
            return False

        # Normalize composite to a plain Python int (bigint-capable)
        try:
            composite = _to_int_like(composite, "composite")
        except Exception:
            return False

        if not isinstance(solution, dict):
            logging.error("Solution is not a dictionary.")
            return False
        if "p" not in solution or "q" not in solution:
            logging.error("Solution does not contain 'p' and 'q' keys.")
            return False

        try:
            p = _to_int_like(solution["p"], "p")
            q = _to_int_like(solution["q"], "q")
        except Exception:
            return False

        # Normalize order (accept either p,q or q,p)
        if p > q:
            p, q = q, p

        # Fast check: product must match
        if p * q != composite:
            logging.error(f"Product of p*q ({p}*{q}={p*q}) does not equal composite ({composite}).")
            return False

        # Primality checks (now that we know the product is correct)
        if not sympy.isprime(p):
            logging.error(f"Factor {p} is not prime.")
            return False
        if not sympy.isprime(q):
            logging.error(f"Factor {q} is not prime.")
            return False

        return True
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
