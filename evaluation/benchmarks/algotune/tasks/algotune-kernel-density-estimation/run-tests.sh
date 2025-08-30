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
PROBLEM_SIZE = 300           # Task difficulty (i.e. "n" in AlgoTune)
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
from typing import Any

import numpy as np
from scipy.stats import multivariate_normal
from sklearn.exceptions import NotFittedError
from sklearn.neighbors import KernelDensity
from numbers import Real



class Solver:
    def __init__(self, **kwargs):
        """
        Initialize the Kernel Density Estimation (KDE) task.

        In this task, given a set of data points X, a set of query points X_q,
        a kernel type, and a bandwidth, the goal is to estimate the probability
        density function from X and evaluate the log-density at the points in X_q.
        """
        super().__init__(**kwargs)
        self.available_kernels = [
            "gaussian",
            "tophat",
            "epanechnikov",
            "exponential",
            "linear",
            "cosine",
        ]

    def _generate_data(
        self, distribution_type: str, num_points: int, dims: int, dist_params: dict | None = None
    ) -> np.ndarray:
        """Internal helper to generate data based on distribution type."""

        if dist_params is None:
            dist_params = {}

        if distribution_type == "normal":
            mean = dist_params.get("mean", np.zeros(dims))
            cov_base = dist_params.get("cov", np.eye(dims))
            # Ensure mean and cov have correct dimensions
            if len(mean) != dims:
                mean = np.zeros(dims)
            cov_base = np.array(cov_base)
            if cov_base.shape != (dims, dims):
                cov_base = np.eye(dims)
            # Add small jitter for numerical stability if cov is identity
            cov = (
                cov_base + np.eye(dims) * 1e-6 if np.allclose(cov_base, np.eye(dims)) else cov_base
            )
            try:
                return np.random.multivariate_normal(mean, cov, size=num_points)
            except np.linalg.LinAlgError:
                logging.warning(
                    "Covariance matrix not positive definite for normal generation, using identity."
                )
                return np.random.multivariate_normal(mean, np.eye(dims), size=num_points)

        elif distribution_type == "uniform":
            low = dist_params.get("low", 0.0)
            high = dist_params.get("high", 1.0)
            return np.random.uniform(low, high, size=(num_points, dims))

        elif distribution_type == "mixture":
            # Expect 'components': List[Tuple[weight, type, params]]
            components = dist_params.get(
                "components",
                [
                    (0.5, "normal", {"mean": np.zeros(dims) - 2, "cov": np.eye(dims) * 0.5}),
                    (0.5, "normal", {"mean": np.zeros(dims) + 2, "cov": np.eye(dims) * 0.5}),
                ],
            )
            logging.debug(f"Generating mixture with components: {components}")
            data = np.zeros((num_points, dims))
            counts = np.random.multinomial(num_points, [comp[0] for comp in components])
            start_idx = 0
            for i, (weight, comp_type, comp_params) in enumerate(components):
                n_comp_points = counts[i]
                if n_comp_points > 0:
                    end_idx = start_idx + n_comp_points
                    # Ensure component parameters match overall dimensions
                    if "mean" in comp_params and len(comp_params["mean"]) != dims:
                        comp_params["mean"] = np.resize(comp_params["mean"], dims)
                        logging.warning(f"Resized mean for component {i} to {dims} dims")
                    if "cov" in comp_params and np.array(comp_params["cov"]).shape != (dims, dims):
                        cov = np.array(comp_params["cov"])
                        comp_params["cov"] = np.resize(cov, (dims, dims)) * np.eye(
                            dims
                        )  # Simplistic resize
                        logging.warning(f"Resized cov for component {i} to {dims}x{dims}")

                    data[start_idx:end_idx, :] = self._generate_data(
                        comp_type, n_comp_points, dims, comp_params
                    )
                    start_idx = end_idx
            return data

        elif distribution_type == "analytical_normal":
            # Same generation as normal, just indicates true density is known
            mean = dist_params.get("mean", np.zeros(dims))
            cov = np.array(dist_params.get("cov", np.eye(dims)))
            if len(mean) != dims:
                mean = np.zeros(dims)
            if cov.shape != (dims, dims):
                cov = np.eye(dims)
            try:
                return np.random.multivariate_normal(mean, cov, size=num_points)
            except np.linalg.LinAlgError:
                logging.warning(
                    "Covariance matrix not positive definite for analytical_normal, using identity."
                )
                return np.random.multivariate_normal(mean, np.eye(dims), size=num_points)

        elif distribution_type == "analytical_uniform":
            # Same generation as uniform
            low = dist_params.get("low", 0.0)
            high = dist_params.get("high", 1.0)
            return np.random.uniform(low, high, size=(num_points, dims))

        else:
            logging.warning(
                f"Unknown distribution type '{distribution_type}'. Falling back to standard normal."
            )
            return np.random.randn(num_points, dims)

    def generate_problem(self, n: int, random_seed: int = 42) -> dict[str, Any]:
        """
        Generate a KDE problem instance.

        The complexity and characteristics (dimensions, sample sizes, distributions,
        kernel, bandwidth) are determined based on the complexity parameter 'n' and
        the random seed.

        :param n: Base scaling parameter controlling complexity.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the KDE problem.
        """
        # Determine parameters based on n and random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Determine parameters: Use n for scaling
        max_dims = 64  # Cap dimensions to prevent excessive runtime
        dims = random.randint(1, min(max(2, n // 2), max_dims))
        num_points = random.randint(n * 5, n * 15)
        num_query_points = random.randint(n, n * 3)
        kernel = random.choice(self.available_kernels)
        # Adjust bandwidth based on dims and n? Maybe just dims.
        bandwidth = (
            random.uniform(0.1, 1.5) * np.sqrt(dims) * (1 + n / 100.0) ** 0.5
        )  # Slightly scale with n

        # Determine distributions and their parameters
        possible_distributions = [
            "normal",
            "uniform",
            "mixture",
            "analytical_normal",
            "analytical_uniform",
        ]
        if n < 10:
            data_distribution = random.choices(
                possible_distributions, weights=[0.4, 0.3, 0.1, 0.1, 0.1], k=1
            )[0]
        else:
            data_distribution = random.choices(
                possible_distributions, weights=[0.3, 0.2, 0.2, 0.15, 0.15], k=1
            )[0]

        dist_params = None
        if data_distribution == "normal" or data_distribution == "analytical_normal":
            mean = np.random.randn(dims) * (n / 10.0)  # Mean scales with n?
            # Generate a random positive semi-definite covariance matrix
            A = np.random.rand(dims, dims)
            cov = np.dot(A, A.transpose()) + np.eye(dims) * 1e-3  # Ensure positive definite
            cov *= 1 + n / 50.0  # Scale covariance with n
            dist_params = {"mean": mean.tolist(), "cov": cov.tolist()}
        elif data_distribution == "uniform" or data_distribution == "analytical_uniform":
            width = 1 + n / 5.0
            center = random.uniform(-n / 10.0, n / 10.0)
            dist_params = {"low": center - width / 2, "high": center + width / 2}
        elif data_distribution == "mixture":
            num_components = random.randint(2, max(3, n // 5))
            components = []
            weights = np.random.dirichlet(np.ones(num_components))  # Random weights summing to 1
            for i in range(num_components):
                comp_type = random.choice(["normal", "uniform"])
                comp_params = {}
                if comp_type == "normal":
                    mean = np.random.randn(dims) * (n / 8.0)
                    A = np.random.rand(dims, dims)
                    cov = np.dot(A, A.transpose()) + np.eye(dims) * 1e-3
                    cov *= (1 + n / 40.0) * random.uniform(0.5, 1.5)  # Vary covariance size
                    comp_params = {"mean": mean.tolist(), "cov": cov.tolist()}
                elif comp_type == "uniform":
                    width = (1 + n / 4.0) * random.uniform(0.5, 1.5)
                    center = random.uniform(-n / 8.0, n / 8.0)
                    comp_params = {"low": center - width / 2, "high": center + width / 2}
                components.append((weights[i], comp_type, comp_params))
            dist_params = {"components": components}

        # Query points generation (can be simpler, e.g., mostly normal/uniform)
        query_distribution = random.choice(["normal", "uniform"])
        query_dist_params = None
        if query_distribution == "normal":
            mean = np.random.randn(dims) * (n / 10.0)
            A = np.random.rand(dims, dims)
            cov = np.dot(A, A.transpose()) + np.eye(dims) * 1e-3
            cov *= 1 + n / 50.0
            query_dist_params = {"mean": mean.tolist(), "cov": cov.tolist()}
        elif query_distribution == "uniform":
            width = 1 + n / 5.0
            center = random.uniform(-n / 10.0, n / 10.0)
            query_dist_params = {"low": center - width / 2, "high": center + width / 2}

        logging.debug(
            f"Generating KDE problem with derived params: n={n}, seed={random_seed}, "
            f"dims={dims}, num_points={num_points}, num_query={num_query_points}, "
            f"kernel={kernel}, bw={bandwidth:.3f}, data_dist={data_distribution}"
        )

        # --- The rest of the generation logic uses the derived parameters ---
        X = self._generate_data(data_distribution, num_points, dims, dist_params)
        X_q = self._generate_data(query_distribution, num_query_points, dims, query_dist_params)

        problem = {
            "data_points": X.tolist(),
            "query_points": X_q.tolist(),
            "kernel": kernel,
            "bandwidth": bandwidth,
        }

        # Optionally add analytical info (existing logic remains the same)
        if data_distribution == "analytical_normal":
            # ... (existing analytical normal logic) ...
            mean = dist_params.get("mean", np.zeros(dims))
            cov = dist_params.get("cov", np.eye(dims))
            cov = np.array(cov)
            mean = np.array(mean)
            if len(mean) != dims:
                mean = np.zeros(dims)
            if cov.shape != (dims, dims):
                cov = np.eye(dims)
            try:
                multivariate_normal(mean=mean, cov=cov, allow_singular=True)
            except Exception as e:
                logging.warning(f"Could not create analytical normal PDF object: {e}")
                problem["data_distribution_type"] = "normal"  # Downgrade if analytical fails

        elif data_distribution == "analytical_uniform":
            # ... (existing analytical uniform logic) ...
            low = dist_params.get("low", 0.0)
            high = dist_params.get("high", 1.0)
            volume = (high - low) ** dims
            if volume <= 0:
                log_density_inside = -np.inf
            else:
                log_density_inside = -np.log(volume)

            def uniform_logpdf(x):
                x = np.asarray(x)
                in_bounds = np.all((x >= low) & (x <= high), axis=-1)
                return np.where(in_bounds, log_density_inside, -np.inf)

        logging.debug(
            f"Generated KDE problem: {num_points} pts, {num_query_points} query, {dims}D, kernel='{kernel}', bw={bandwidth:.3f}, data_dist='{data_distribution}'"
        )
        return problem

    def solve(
        self, problem: dict[str, Any]
    ) -> dict[str, Any]:  # Return type includes error possibility
        try:
            X = np.array(problem["data_points"])
            X_q = np.array(problem["query_points"])
            kernel = problem["kernel"]
            bandwidth = problem["bandwidth"]
            # Infer dimensions from data robustly
            if X.ndim != 2 or X_q.ndim != 2:
                raise ValueError("Data points or query points are not 2D arrays.")
            if X.shape[0] == 0:
                raise ValueError("No data points provided.")
            if X_q.shape[0] == 0:
                # Return empty list if no query points
                return {"log_density": []}
            if X.shape[1] != X_q.shape[1]:
                raise ValueError("Data points and query points have different dimensions.")

            # Basic validation of inputs needed for solving
            if not isinstance(bandwidth, Real) or bandwidth <= 0:
                raise ValueError("Bandwidth must be positive.")
            bandwidth = float(bandwidth)
            if kernel not in self.available_kernels:
                raise ValueError(f"Unknown kernel: {kernel}")

            # Initialize and fit the KDE model
            kde = KernelDensity(kernel=kernel, bandwidth=bandwidth)
            kde.fit(X)

            # Evaluate the log-density at query points
            log_density = kde.score_samples(X_q)

            solution = {"log_density": log_density.tolist()}
            return solution

        except KeyError as e:
            logging.error(f"Missing key in problem dictionary: {e}")
            return {"error": f"Missing key: {e}"}
        except (ValueError, TypeError, NotFittedError, np.linalg.LinAlgError) as e:
            logging.error(f"Error during KDE computation: {e}")
            return {"error": f"Computation error: {e}"}
        except Exception as e:
            logging.error(f"An unexpected error occurred during solve: {e}", exc_info=True)
            return {"error": f"Unexpected error: {e}"}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, list[float]]) -> bool:
        """
        Validate the KDE solution against a reference computed with `self.solve`.

        Improvements:
        - Accept any empty array-like for zero query points.
        - Squeeze shapes so (n, 1) is treated as (n,).
        - Require identical non-finite masks (e.g., -inf where the reference has -inf).
        - Compare only finite entries with slightly relaxed tolerances.
        """
        # 0) Student signaled error
        if "error" in solution:
            logging.error(f"Solution indicates an error state: {solution['error']}")
            return False

        # 1) Problem structure checks
        for key in ("data_points", "query_points", "kernel", "bandwidth"):
            if key not in problem:
                logging.error(f"Problem dictionary is missing the key: '{key}'.")
                return False

        # 2) Query points → expected length
        try:
            query_points = np.asarray(problem["query_points"])
        except Exception as e:
            logging.error(f"Failed to parse 'query_points' from problem: {e}")
            return False
        if query_points.ndim != 2:
            logging.error(
                f"'query_points' must be 2D (n_samples, n_features), got ndim={query_points.ndim}."
            )
            return False
        num_query_points = int(query_points.shape[0])

        # 3) Parse student's output; handle zero-query case
        if "log_density" not in solution:
            logging.error("Solution does not contain 'log_density' key.")
            return False
        try:
            log_density_sol = np.asarray(solution["log_density"], dtype=float)
        except Exception as e:
            logging.error(f"Could not convert solution['log_density'] to float array: {e}")
            return False

        if num_query_points == 0:
            # Accept any empty array-like (not just list)
            if log_density_sol.size == 0:
                logging.debug("Validation successful for zero query points (empty output).")
                return True
            logging.error("Expected empty 'log_density' for zero query points.")
            return False

        # 4) Shape robustness: squeeze → enforce 1-D of correct length
        log_density_sol = np.squeeze(log_density_sol)
        if log_density_sol.ndim != 1 or log_density_sol.shape[0] != num_query_points:
            logging.error(
                f"Solution 'log_density' has incorrect shape. "
                f"Expected ({num_query_points},) after squeeze, got {log_density_sol.shape}."
            )
            return False

        # 5) Compute reference
        reference_solution = self.solve(problem)
        if "error" in reference_solution:
            logging.error(
                f"Failed to compute reference solution for validation: {reference_solution['error']}"
            )
            return False

        try:
            log_density_ref = np.asarray(reference_solution["log_density"], dtype=float)
        except Exception as e:
            logging.error(f"Could not convert reference 'log_density' to float array: {e}")
            return False

        log_density_ref = np.squeeze(log_density_ref)
        if log_density_ref.ndim != 1 or log_density_ref.shape[0] != num_query_points:
            logging.error(
                f"Reference 'log_density' has unexpected shape {log_density_ref.shape}; "
                f"expected ({num_query_points},)."
            )
            return False

        # 6) Robust comparison:
        #    a) Non-finite masks (e.g., -inf at zero density) must match exactly.
        ref_nonfinite = ~np.isfinite(log_density_ref)
        sol_nonfinite = ~np.isfinite(log_density_sol)
        if not np.array_equal(ref_nonfinite, sol_nonfinite):
            bad_idx = np.where(ref_nonfinite != sol_nonfinite)[0][:5]
            logging.error(
                "Non-finite pattern mismatch. "
                f"First differing indices (sample): {bad_idx.tolist()}; "
                f"ref_nonfinite_count={int(ref_nonfinite.sum())}, "
                f"sol_nonfinite_count={int(sol_nonfinite.sum())}."
            )
            return False

        #    b) Compare only finite entries with reasonable tolerances.
        finite_mask = np.isfinite(log_density_ref)  # same mask for solution now
        ref_f = log_density_ref[finite_mask]
        sol_f = log_density_sol[finite_mask]

        if ref_f.size == 0:
            # Everything is non-finite but masks matched (e.g., all -inf) → accept
            return True

        rtol, atol = 1e-4, 1e-6  # still strict, but avoids false negatives near support boundaries
        if not np.allclose(sol_f, ref_f, rtol=rtol, atol=atol):
            # Diagnostics ONLY on finite entries to avoid inf - inf → NaN noise
            max_abs_diff = float(np.max(np.abs(sol_f - ref_f)))
            max_rel_diff = float(np.max(np.abs((sol_f - ref_f) / (np.abs(ref_f) + 1e-12))))
            logging.error(
                "Solution 'log_density' does not match reference within tolerance "
                f"(rtol={rtol}, atol={atol}). Max abs diff: {max_abs_diff:.4e}, "
                f"Max rel diff: {max_rel_diff:.4e}."
            )
            return False

        return True
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
pytest /workspace/test_outputs.py -rA -s

# --- Step 7: Exit ---
# The script has completed its execution.
echo "Script finished."
