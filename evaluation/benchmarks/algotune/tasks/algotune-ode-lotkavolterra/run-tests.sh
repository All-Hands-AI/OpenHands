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
PROBLEM_SIZE = 161           # Task difficulty (i.e. "n" in AlgoTune)
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
import math

try:
    from numba import njit  # type: ignore
    NUMBA_AVAILABLE = True
except Exception:  # pragma: no cover
    NUMBA_AVAILABLE = False

def _integrate_lv_py(
    t0: float,
    t1: float,
    x0: float,
    y0: float,
    alpha: float,
    beta: float,
    delta: float,
    gamma: float,
    rtol: float,
    atol: float,
) -> List[float]:
    # Handle axis-invariant closed forms quickly
    dt = t1 - t0
    if y0 == 0.0:
        # y stays zero, x grows exponentially with rate alpha
        x = x0 * math.exp(alpha * dt)
        return [x if x >= 0.0 else 0.0, 0.0]
    if x0 == 0.0:
        # x stays zero, y decays exponentially with rate gamma
        y = y0 * math.exp(-gamma * dt)
        return [0.0, y if y >= 0.0 else 0.0]

    # Direction of integration
    t = t0
    tf = t1
    x = x0
    y = y0
    h_sign = 1.0 if tf >= t else -1.0
    h_max = abs(tf - t)

    # Dormand-Prince RK45 coefficients
    a21 = 1.0 / 5.0

    a31 = 3.0 / 40.0
    a32 = 9.0 / 40.0

    a41 = 44.0 / 45.0
    a42 = -56.0 / 15.0
    a43 = 32.0 / 9.0

    a51 = 19372.0 / 6561.0
    a52 = -25360.0 / 2187.0
    a53 = 64448.0 / 6561.0
    a54 = -212.0 / 729.0

    a61 = 9017.0 / 3168.0
    a62 = -355.0 / 33.0
    a63 = 46732.0 / 5247.0
    a64 = 49.0 / 176.0
    a65 = -5103.0 / 18656.0

    # Fifth order solution weights
    b1 = 35.0 / 384.0
    b3 = 500.0 / 1113.0
    b4 = 125.0 / 192.0
    b5 = -2187.0 / 6784.0
    b6 = 11.0 / 84.0

    # Fourth order solution weights (for error estimate)
    bs1 = 5179.0 / 57600.0
    bs3 = 7571.0 / 16695.0
    bs4 = 393.0 / 640.0
    bs5 = -92097.0 / 339200.0
    bs6 = 187.0 / 2100.0
    bs7 = 1.0 / 40.0

    safety = 0.9
    fac_min = 0.2
    fac_max = 5.0
    order = 5.0  # for step-size control exponent 1/order

    # Helper derivative
    def fxy(xx: float, yy: float):
        return (alpha - beta * yy) * xx, (delta * xx - gamma) * yy

    # Initial derivative and step size heuristic
    k1x, k1y = fxy(x, y)
    sx = atol + rtol * abs(x)
    sy = atol + rtol * abs(y)
    d0 = math.hypot(x / sx, y / sy)
    d1 = math.hypot(k1x / sx, k1y / sy)
    if d0 < 1e-5 or d1 < 1e-5:
        h = 1e-6
    else:
        h = 0.01 * d0 / d1
    if h > h_max:
        h = h_max
    h *= h_sign

    # Try improving initial step using an Euler trial
    xe = x + h * k1x
    ye = y + h * k1y
    k1x_e, k1y_e = fxy(xe, ye)
    d2 = math.hypot((k1x_e - k1x) / sx, (k1y_e - k1y) / sy) / max(abs(h), 1e-16)
    if max(d1, d2) > 1e-15:
        h = min(h_max, (0.01 / max(d1, d2)))
        h *= h_sign

    h_min = 1e-16 * h_sign
    have_k1 = True

    # Integration loop
    # Limit steps to avoid infinite loops in pathological cases
    n_steps = 0
    n_steps_max = 10_000_000
    while (t - tf) * h_sign < 0.0 and n_steps < n_steps_max:
        n_steps += 1
        h = min(abs(h), abs(tf - t)) * h_sign
        if abs(h) < abs(h_min):
            break

        # Stage 1
        if not have_k1:
            k1x, k1y = fxy(x, y)

        # Stage 2
        y2x = x + h * a21 * k1x
        y2y = y + h * a21 * k1y
        k2x, k2y = fxy(y2x, y2y)

        # Stage 3
        y3x = x + h * (a31 * k1x + a32 * k2x)
        y3y = y + h * (a31 * k1y + a32 * k2y)
        k3x, k3y = fxy(y3x, y3y)

        # Stage 4
        y4x = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
        y4y = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
        k4x, k4y = fxy(y4x, y4y)

        # Stage 5
        y5x = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
        y5y = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
        k5x, k5y = fxy(y5x, y5y)

        # Stage 6
        y6x = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
        y6y = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
        k6x, k6y = fxy(y6x, y6y)

        # 5th order solution (y_next), omit zero-weight terms
        y5nx = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
        y5ny = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

        # Stage 7 for error estimate (uses y5n and provides FSAL for next step)
        k7x, k7y = fxy(y5nx, y5ny)

        # 4th order solution for error estimate (omit zero-weight terms)
        y4nx = x + h * (bs1 * k1x + bs3 * k3x + bs4 * k4x + bs5 * k5x + bs6 * k6x + bs7 * k7x)
        y4ny = y + h * (bs1 * k1y + bs3 * k3y + bs4 * k4y + bs5 * k5y + bs6 * k6y + bs7 * k7y)

        # Error estimate without sqrt: err2 = 0.5 * (ex^2 + ey^2)
        ax = abs(y5nx)
        if ax < abs(x):
            ax = abs(x)
        ay = abs(y5ny)
        if ay < abs(y):
            ay = abs(y)
        scale_x = atol + rtol * ax
        scale_y = atol + rtol * ay
        ex = (y5nx - y4nx) / scale_x
        ey = (y5ny - y4ny) / scale_y
        err2 = 0.5 * (ex * ex + ey * ey)

        if err2 <= 1.0:
            # Accept step
            t += h
            x, y = y5nx, y5ny
            # FSAL: next step k1 is current k7
            k1x, k1y = k7x, k7y
            have_k1 = True

            # Step size update
            if err2 == 0.0:
                fac = fac_max
            else:
                fac = safety * (err2 ** (-0.1))  # (-1/5) with sqrt removed
                if fac < fac_min:
                    fac = fac_min
                elif fac > fac_max:
                    fac = fac_max
            h *= fac
        else:
            # Reject step: decrease step size, do not advance
            have_k1 = False
            fac = safety * (err2 ** (-0.1))
            if fac < fac_min:
                fac = fac_min
            h *= fac

    # Final non-negative guard (tiny negatives due to round-off)
    if x < 0.0:
        x = 0.0
    if y < 0.0:
        y = 0.0

    return [x, y]

# Numba-accelerated version (compiled on first call)
if NUMBA_AVAILABLE:
    @njit(cache=True, fastmath=True, nogil=True)
    def _integrate_lv_numba(
        t0: float,
        t1: float,
        x0: float,
        y0: float,
        alpha: float,
        beta: float,
        delta: float,
        gamma: float,
        rtol: float,
        atol: float,
    ):
        # Handle axis-invariant closed forms quickly
        dt = t1 - t0
        if y0 == 0.0:
            x = x0 * math.exp(alpha * dt)
            if x < 0.0:
                x = 0.0
            return x, 0.0
        if x0 == 0.0:
            y = y0 * math.exp(-gamma * dt)
            if y < 0.0:
                y = 0.0
            return 0.0, y

        t = t0
        tf = t1
        x = x0
        y = y0
        h_sign = 1.0 if tf >= t else -1.0
        h_max = tf - t
        if h_max < 0.0:
            h_max = -h_max

        # Dormand-Prince RK45 coefficients
        a21 = 1.0 / 5.0

        a31 = 3.0 / 40.0
        a32 = 9.0 / 40.0

        a41 = 44.0 / 45.0
        a42 = -56.0 / 15.0
        a43 = 32.0 / 9.0

        a51 = 19372.0 / 6561.0
        a52 = -25360.0 / 2187.0
        a53 = 64448.0 / 6561.0
        a54 = -212.0 / 729.0

        a61 = 9017.0 / 3168.0
        a62 = -355.0 / 33.0
        a63 = 46732.0 / 5247.0
        a64 = 49.0 / 176.0
        a65 = -5103.0 / 18656.0

        b1 = 35.0 / 384.0
        b3 = 500.0 / 1113.0
        b4 = 125.0 / 192.0
        b5 = -2187.0 / 6784.0
        b6 = 11.0 / 84.0

        bs1 = 5179.0 / 57600.0
        bs3 = 7571.0 / 16695.0
        bs4 = 393.0 / 640.0
        bs5 = -92097.0 / 339200.0
        bs6 = 187.0 / 2100.0
        bs7 = 1.0 / 40.0

        safety = 0.9
        fac_min = 0.2
        fac_max = 5.0
        order = 5.0  # unused, replaced with exponent -0.2 via err2 ** -0.1

        # Initial derivative and step size heuristic
        # k1
        k1x = (alpha - beta * y) * x
        k1y = (delta * x - gamma) * y
        ax = x if x >= 0.0 else -x
        ay = y if y >= 0.0 else -y
        sx = atol + rtol * ax
        sy = atol + rtol * ay
        d0 = math.sqrt((x / sx) * (x / sx) + (y / sy) * (y / sy))
        d1 = math.sqrt((k1x / sx) * (k1x / sx) + (k1y / sy) * (k1y / sy))
        h = 1e-6 if (d0 < 1e-5 or d1 < 1e-5) else (0.01 * d0 / d1)
        if h > h_max:
            h = h_max
        h *= h_sign

        # Try improving initial step using an Euler trial
        xe = x + h * k1x
        ye = y + h * k1y
        k1x_e = (alpha - beta * ye) * xe
        k1y_e = (delta * xe - gamma) * ye
        ah = h if h >= 0.0 else -h
        if ah < 1e-16:
            ah = 1e-16
        d2 = math.sqrt(((k1x_e - k1x) / sx) ** 2 + ((k1y_e - k1y) / sy) ** 2) / ah
        m = d1 if d1 > d2 else d2
        if m > 1e-15:
            hh = 0.01 / m
            if hh > h_max:
                hh = h_max
            h = hh * h_sign

        h_min = 1e-16 * h_sign
        have_k1 = True

        n_steps = 0
        n_steps_max = 10000000
        while (t - tf) * h_sign < 0.0 and n_steps < n_steps_max:
            n_steps += 1
            ah = h if h >= 0.0 else -h
            rem = tf - t
            if rem < 0.0:
                rem = -rem
            if ah > rem:
                h = rem if h >= 0.0 else -rem
            if (h if h >= 0.0 else -h) < (h_min if h_min >= 0.0 else -h_min):
                break

            # Stage 1
            if not have_k1:
                k1x = (alpha - beta * y) * x
                k1y = (delta * x - gamma) * y

            # Stage 2
            y2x = x + h * a21 * k1x
            y2y = y + h * a21 * k1y
            k2x = (alpha - beta * y2y) * y2x
            k2y = (delta * y2x - gamma) * y2y

            # Stage 3
            y3x = x + h * (a31 * k1x + a32 * k2x)
            y3y = y + h * (a31 * k1y + a32 * k2y)
            k3x = (alpha - beta * y3y) * y3x
            k3y = (delta * y3x - gamma) * y3y

            # Stage 4
            y4x = x + h * (a41 * k1x + a42 * k2x + a43 * k3x)
            y4y = y + h * (a41 * k1y + a42 * k2y + a43 * k3y)
            k4x = (alpha - beta * y4y) * y4x
            k4y = (delta * y4x - gamma) * y4y

            # Stage 5
            y5x = x + h * (a51 * k1x + a52 * k2x + a53 * k3x + a54 * k4x)
            y5y = y + h * (a51 * k1y + a52 * k2y + a53 * k3y + a54 * k4y)
            k5x = (alpha - beta * y5y) * y5x
            k5y = (delta * y5x - gamma) * y5y

            # Stage 6
            y6x = x + h * (a61 * k1x + a62 * k2x + a63 * k3x + a64 * k4x + a65 * k5x)
            y6y = y + h * (a61 * k1y + a62 * k2y + a63 * k3y + a64 * k4y + a65 * k5y)
            k6x = (alpha - beta * y6y) * y6x
            k6y = (delta * y6x - gamma) * y6y

            # 5th order solution (y_next), omit zero-weight terms
            y5nx = x + h * (b1 * k1x + b3 * k3x + b4 * k4x + b5 * k5x + b6 * k6x)
            y5ny = y + h * (b1 * k1y + b3 * k3y + b4 * k4y + b5 * k5y + b6 * k6y)

            # Stage 7 for error estimate (FSAL next step)
            k7x = (alpha - beta * y5ny) * y5nx
            k7y = (delta * y5nx - gamma) * y5ny

            # 4th order solution for error estimate (omit zero-weight terms)
            y4nx = x + h * (bs1 * k1x + bs3 * k3x + bs4 * k4x + bs5 * k5x + bs6 * k6x + bs7 * k7x)
            y4ny = y + h * (bs1 * k1y + bs3 * k3y + bs4 * k4y + bs5 * k5y + bs6 * k6y + bs7 * k7y)

            ax = y5nx if y5nx >= 0.0 else -y5nx
            bx = x if x >= 0.0 else -x
            if ax < bx:
                ax = bx
            ay = y5ny if y5ny >= 0.0 else -y5ny
            by = y if y >= 0.0 else -y
            if ay < by:
                ay = by
            scale_x = atol + rtol * ax
            scale_y = atol + rtol * ay
            ex = (y5nx - y4nx) / scale_x
            ey = (y5ny - y4ny) / scale_y
            err2 = 0.5 * (ex * ex + ey * ey)

            if err2 <= 1.0:
                t += h
                x = y5nx
                y = y5ny
                k1x = k7x
                k1y = k7y
                have_k1 = True

                if err2 == 0.0:
                    fac = fac_max
                else:
                    fac = safety * (err2 ** (-0.1))
                    if fac < fac_min:
                        fac = fac_min
                    elif fac > fac_max:
                        fac = fac_max
                h *= fac
            else:
                have_k1 = False
                fac = safety * (err2 ** (-0.1))
                if fac < fac_min:
                    fac = fac_min
                h *= fac

        if x < 0.0:
            x = 0.0
        if y < 0.0:
            y = 0.0
        return x, y

class Solver:
    def solve(self, problem: Dict[str, Any], **kwargs) -> List[float]:
        # Extract inputs
        t0: float = float(problem["t0"])
        t1: float = float(problem["t1"])
        y0 = problem["y0"]
        x = float(y0[0])
        y = float(y0[1])

        params = problem["params"]
        alpha = float(params["alpha"])
        beta = float(params["beta"])
        delta = float(params["delta"])
        gamma = float(params["gamma"])

        if t1 == t0:
            # No integration needed
            if x < 0.0:
                x = 0.0
            if y < 0.0:
                y = 0.0
            return [x, y]

        # Axis-invariant closed forms
        dt = t1 - t0
        if y == 0.0:
            xf = x * math.exp(alpha * dt)
            return [xf if xf >= 0.0 else 0.0, 0.0]
        if x == 0.0:
            yf = y * math.exp(-gamma * dt)
            return [0.0, yf if yf >= 0.0 else 0.0]

        # Tolerances (can be overridden)
        rtol = float(kwargs.get("rtol", 1e-8))
        atol = float(kwargs.get("atol", 1e-10))

        if NUMBA_AVAILABLE:
            xf, yf = _integrate_lv_numba(t0, t1, x, y, alpha, beta, delta, gamma, rtol, atol)
            return [xf if xf >= 0.0 else 0.0, yf if yf >= 0.0 else 0.0]
        else:
            return _integrate_lv_py(t0, t1, x, y, alpha, beta, delta, gamma, rtol, atol)
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
