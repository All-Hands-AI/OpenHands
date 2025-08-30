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
PROBLEM_SIZE = 12           # Task difficulty (i.e. "n" in AlgoTune)
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
cat > /workspace/setup.py << 'EOF'
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("solver_c", ["solver_c.pyx"], extra_compile_args=["-O3"])
]

setup(
    name="solver_c",
    ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"}),
)
EOF

cat > /workspace/solver.py << 'EOF'
try:
    from solver_c import solve_c as _solve_c
    has_c = True
except ImportError:
    _solve_c = None
    has_c = False
class Solver:
    def solve(self, problem, **kwargs):
        if has_c:
            return _solve_c(problem)
        # Maximum Independent Set via maximum clique in complement graph (bitset Branch & Bound)
        n = len(problem)
        # build complement neighbor bitsets
        neighbors = [0] * n
        full_mask = (1 << n) - 1
        for i in range(n):
            mask = full_mask & ~(1 << i)
            row = problem[i]
            for j in range(n):
                if row[j]:
                    mask &= ~(1 << j)
            neighbors[i] = mask
        # initial greedy clique in complement graph for lower bound
        order = sorted(range(n), key=lambda x: neighbors[x].bit_count())
        greedyR = 0
        for v in order:
            if (greedyR & ~neighbors[v]) == 0:
                greedyR |= (1 << v)
        bestR = greedyR
        best_size = greedyR.bit_count()
        # increase recursion limit
        import sys
        sys.setrecursionlimit(10000)
        # Branch & Bound recursion (Bron–Kerbosch with pivot)
        def bk(R, P, X):
            nonlocal bestR, best_size
            if P == 0 and X == 0:
                sz = R.bit_count()
                if sz > best_size:
                    best_size = sz
                    bestR = R
                return
            # bound: no possible improvement
            if R.bit_count() + P.bit_count() <= best_size:
                return
            # choose pivot u from P|X to minimize branches
            PU = P | X
            maxd = -1
            u = 0
            tmp = PU
            while tmp:
                v = tmp & -tmp
                tmp ^= v
                idx = v.bit_length() - 1
                d = (P & neighbors[idx]).bit_count()
                if d > maxd:
                    maxd = d
                    u = idx
            # branch on vertices not adjacent to pivot
            ext = P & ~neighbors[u]
            tmp = ext
            while tmp:
                v = tmp & -tmp
                tmp ^= v
                idx = v.bit_length() - 1
                vk = 1 << idx
                bk(R | vk, P & neighbors[idx], X & neighbors[idx])
                P &= ~vk
                X |= vk
        # initial call
        bk(0, full_mask, 0)
        # extract result vertices
        return [i for i in range(n) if (bestR >> i) & 1]
EOF

cat > /workspace/solver_c.c << 'EOF'
/* Generated by Cython 3.1.2 */

/* BEGIN: Cython Metadata
{
    "distutils": {
        "depends": [],
        "extra_compile_args": [
            "-O3"
        ],
        "name": "solver_c",
        "sources": [
            "solver_c.pyx"
        ]
    },
    "module_name": "solver_c"
}
END: Cython Metadata */

#ifndef PY_SSIZE_T_CLEAN
#define PY_SSIZE_T_CLEAN
#endif /* PY_SSIZE_T_CLEAN */
/* InitLimitedAPI */
#if defined(Py_LIMITED_API) && !defined(CYTHON_LIMITED_API)
  #define CYTHON_LIMITED_API 1
#endif

#include "Python.h"
#ifndef Py_PYTHON_H
    #error Python headers needed to compile C extensions, please install development version of Python.
#elif PY_VERSION_HEX < 0x03080000
    #error Cython requires Python 3.8+.
#else
#define __PYX_ABI_VERSION "3_1_2"
#define CYTHON_HEX_VERSION 0x030102F0
#define CYTHON_FUTURE_DIVISION 1
/* CModulePreamble */
#include <stddef.h>
#ifndef offsetof
  #define offsetof(type, member) ( (size_t) & ((type*)0) -> member )
#endif
#if !defined(_WIN32) && !defined(WIN32) && !defined(MS_WINDOWS)
  #ifndef __stdcall
    #define __stdcall
  #endif
  #ifndef __cdecl
    #define __cdecl
  #endif
  #ifndef __fastcall
    #define __fastcall
  #endif
#endif
#ifndef DL_IMPORT
  #define DL_IMPORT(t) t
#endif
#ifndef DL_EXPORT
  #define DL_EXPORT(t) t
#endif
#define __PYX_COMMA ,
#ifndef HAVE_LONG_LONG
  #define HAVE_LONG_LONG
#endif
#ifndef PY_LONG_LONG
  #define PY_LONG_LONG LONG_LONG
#endif
#ifndef Py_HUGE_VAL
  #define Py_HUGE_VAL HUGE_VAL
#endif
#define __PYX_LIMITED_VERSION_HEX PY_VERSION_HEX
#if defined(GRAALVM_PYTHON)
  /* For very preliminary testing purposes. Most variables are set the same as PyPy.
     The existence of this section does not imply that anything works or is even tested */
  #define CYTHON_COMPILING_IN_PYPY 0
  #define CYTHON_COMPILING_IN_CPYTHON 0
  #define CYTHON_COMPILING_IN_LIMITED_API 0
  #define CYTHON_COMPILING_IN_GRAAL 1
  #define CYTHON_COMPILING_IN_CPYTHON_FREETHREADING 0
  #undef CYTHON_USE_TYPE_SLOTS
  #define CYTHON_USE_TYPE_SLOTS 0
  #undef CYTHON_USE_TYPE_SPECS
  #define CYTHON_USE_TYPE_SPECS 0
  #undef CYTHON_USE_PYTYPE_LOOKUP
  #define CYTHON_USE_PYTYPE_LOOKUP 0
  #undef CYTHON_USE_PYLIST_INTERNALS
  #define CYTHON_USE_PYLIST_INTERNALS 0
  #undef CYTHON_USE_UNICODE_INTERNALS
  #define CYTHON_USE_UNICODE_INTERNALS 0
  #undef CYTHON_USE_UNICODE_WRITER
  #define CYTHON_USE_UNICODE_WRITER 0
  #undef CYTHON_USE_PYLONG_INTERNALS
  #define CYTHON_USE_PYLONG_INTERNALS 0
  #undef CYTHON_AVOID_BORROWED_REFS
  #define CYTHON_AVOID_BORROWED_REFS 1
  #undef CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
  #define CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS 1
  #undef CYTHON_ASSUME_SAFE_MACROS
  #define CYTHON_ASSUME_SAFE_MACROS 0
  #undef CYTHON_ASSUME_SAFE_SIZE
  #define CYTHON_ASSUME_SAFE_SIZE 0
  #undef CYTHON_UNPACK_METHODS
  #define CYTHON_UNPACK_METHODS 0
  #undef CYTHON_FAST_THREAD_STATE
  #define CYTHON_FAST_THREAD_STATE 0
  #undef CYTHON_FAST_GIL
  #define CYTHON_FAST_GIL 0
  #undef CYTHON_METH_FASTCALL
  #define CYTHON_METH_FASTCALL 0
  #undef CYTHON_FAST_PYCALL
  #define CYTHON_FAST_PYCALL 0
  #ifndef CYTHON_PEP487_INIT_SUBCLASS
    #define CYTHON_PEP487_INIT_SUBCLASS 1
  #endif
  #undef CYTHON_PEP489_MULTI_PHASE_INIT
  #define CYTHON_PEP489_MULTI_PHASE_INIT 1
  #undef CYTHON_USE_MODULE_STATE
  #define CYTHON_USE_MODULE_STATE 0
  #undef CYTHON_USE_SYS_MONITORING
  #define CYTHON_USE_SYS_MONITORING 0
  #undef CYTHON_USE_TP_FINALIZE
  #define CYTHON_USE_TP_FINALIZE 0
  #undef CYTHON_USE_AM_SEND
  #define CYTHON_USE_AM_SEND 0
  #undef CYTHON_USE_DICT_VERSIONS
  #define CYTHON_USE_DICT_VERSIONS 0
  #undef CYTHON_USE_EXC_INFO_STACK
  #define CYTHON_USE_EXC_INFO_STACK 1
  #ifndef CYTHON_UPDATE_DESCRIPTOR_DOC
    #define CYTHON_UPDATE_DESCRIPTOR_DOC 0
  #endif
  #undef CYTHON_USE_FREELISTS
  #define CYTHON_USE_FREELISTS 0
#elif defined(PYPY_VERSION)
  #define CYTHON_COMPILING_IN_PYPY 1
  #define CYTHON_COMPILING_IN_CPYTHON 0
  #define CYTHON_COMPILING_IN_LIMITED_API 0
  #define CYTHON_COMPILING_IN_GRAAL 0
  #define CYTHON_COMPILING_IN_CPYTHON_FREETHREADING 0
  #undef CYTHON_USE_TYPE_SLOTS
  #define CYTHON_USE_TYPE_SLOTS 1
  #ifndef CYTHON_USE_TYPE_SPECS
    #define CYTHON_USE_TYPE_SPECS 0
  #endif
  #undef CYTHON_USE_PYTYPE_LOOKUP
  #define CYTHON_USE_PYTYPE_LOOKUP 0
  #undef CYTHON_USE_PYLIST_INTERNALS
  #define CYTHON_USE_PYLIST_INTERNALS 0
  #undef CYTHON_USE_UNICODE_INTERNALS
  #define CYTHON_USE_UNICODE_INTERNALS 0
  #undef CYTHON_USE_UNICODE_WRITER
  #define CYTHON_USE_UNICODE_WRITER 0
  #undef CYTHON_USE_PYLONG_INTERNALS
  #define CYTHON_USE_PYLONG_INTERNALS 0
  #undef CYTHON_AVOID_BORROWED_REFS
  #define CYTHON_AVOID_BORROWED_REFS 1
  #undef CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
  #define CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS 1
  #undef CYTHON_ASSUME_SAFE_MACROS
  #define CYTHON_ASSUME_SAFE_MACROS 0
  #ifndef CYTHON_ASSUME_SAFE_SIZE
    #define CYTHON_ASSUME_SAFE_SIZE 1
  #endif
  #undef CYTHON_UNPACK_METHODS
  #define CYTHON_UNPACK_METHODS 0
  #undef CYTHON_FAST_THREAD_STATE
  #define CYTHON_FAST_THREAD_STATE 0
  #undef CYTHON_FAST_GIL
  #define CYTHON_FAST_GIL 0
  #undef CYTHON_METH_FASTCALL
  #define CYTHON_METH_FASTCALL 0
  #undef CYTHON_FAST_PYCALL
  #define CYTHON_FAST_PYCALL 0
  #ifndef CYTHON_PEP487_INIT_SUBCLASS
    #define CYTHON_PEP487_INIT_SUBCLASS 1
  #endif
  #if PY_VERSION_HEX < 0x03090000
    #undef CYTHON_PEP489_MULTI_PHASE_INIT
    #define CYTHON_PEP489_MULTI_PHASE_INIT 0
  #elif !defined(CYTHON_PEP489_MULTI_PHASE_INIT)
    #define CYTHON_PEP489_MULTI_PHASE_INIT 1
  #endif
  #undef CYTHON_USE_MODULE_STATE
  #define CYTHON_USE_MODULE_STATE 0
  #undef CYTHON_USE_SYS_MONITORING
  #define CYTHON_USE_SYS_MONITORING 0
  #ifndef CYTHON_USE_TP_FINALIZE
    #define CYTHON_USE_TP_FINALIZE (PYPY_VERSION_NUM >= 0x07030C00)
  #endif
  #undef CYTHON_USE_AM_SEND
  #define CYTHON_USE_AM_SEND 0
  #undef CYTHON_USE_DICT_VERSIONS
  #define CYTHON_USE_DICT_VERSIONS 0
  #undef CYTHON_USE_EXC_INFO_STACK
  #define CYTHON_USE_EXC_INFO_STACK 0
  #ifndef CYTHON_UPDATE_DESCRIPTOR_DOC
    #define CYTHON_UPDATE_DESCRIPTOR_DOC (PYPY_VERSION_NUM >= 0x07031100)
  #endif
  #undef CYTHON_USE_FREELISTS
  #define CYTHON_USE_FREELISTS 0
#elif defined(CYTHON_LIMITED_API)
  #ifdef Py_LIMITED_API
    #undef __PYX_LIMITED_VERSION_HEX
    #define __PYX_LIMITED_VERSION_HEX Py_LIMITED_API
  #endif
  #define CYTHON_COMPILING_IN_PYPY 0
  #define CYTHON_COMPILING_IN_CPYTHON 0
  #define CYTHON_COMPILING_IN_LIMITED_API 1
  #define CYTHON_COMPILING_IN_GRAAL 0
  #define CYTHON_COMPILING_IN_CPYTHON_FREETHREADING 0
  #undef CYTHON_CLINE_IN_TRACEBACK
  #define CYTHON_CLINE_IN_TRACEBACK 0
  #undef CYTHON_USE_TYPE_SLOTS
  #define CYTHON_USE_TYPE_SLOTS 0
  #undef CYTHON_USE_TYPE_SPECS
  #define CYTHON_USE_TYPE_SPECS 1
  #undef CYTHON_USE_PYTYPE_LOOKUP
  #define CYTHON_USE_PYTYPE_LOOKUP 0
  #undef CYTHON_USE_PYLIST_INTERNALS
  #define CYTHON_USE_PYLIST_INTERNALS 0
  #undef CYTHON_USE_UNICODE_INTERNALS
  #define CYTHON_USE_UNICODE_INTERNALS 0
  #ifndef CYTHON_USE_UNICODE_WRITER
    #define CYTHON_USE_UNICODE_WRITER 0
  #endif
  #undef CYTHON_USE_PYLONG_INTERNALS
  #define CYTHON_USE_PYLONG_INTERNALS 0
  #ifndef CYTHON_AVOID_BORROWED_REFS
    #define CYTHON_AVOID_BORROWED_REFS 0
  #endif
  #ifndef CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
    #define CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS 0
  #endif
  #undef CYTHON_ASSUME_SAFE_MACROS
  #define CYTHON_ASSUME_SAFE_MACROS 0
  #undef CYTHON_ASSUME_SAFE_SIZE
  #define CYTHON_ASSUME_SAFE_SIZE 0
  #undef CYTHON_UNPACK_METHODS
  #define CYTHON_UNPACK_METHODS 0
  #undef CYTHON_FAST_THREAD_STATE
  #define CYTHON_FAST_THREAD_STATE 0
  #undef CYTHON_FAST_GIL
  #define CYTHON_FAST_GIL 0
  #undef CYTHON_METH_FASTCALL
  #define CYTHON_METH_FASTCALL (__PYX_LIMITED_VERSION_HEX >= 0x030C0000)
  #undef CYTHON_FAST_PYCALL
  #define CYTHON_FAST_PYCALL 0
  #ifndef CYTHON_PEP487_INIT_SUBCLASS
    #define CYTHON_PEP487_INIT_SUBCLASS 1
  #endif
  #ifndef CYTHON_PEP489_MULTI_PHASE_INIT
    #define CYTHON_PEP489_MULTI_PHASE_INIT 1
  #endif
  #ifndef CYTHON_USE_MODULE_STATE
    #define CYTHON_USE_MODULE_STATE 0
  #endif
  #undef CYTHON_USE_SYS_MONITORING
  #define CYTHON_USE_SYS_MONITORING 0
  #ifndef CYTHON_USE_TP_FINALIZE
    #define CYTHON_USE_TP_FINALIZE 0
  #endif
  #ifndef CYTHON_USE_AM_SEND
    #define CYTHON_USE_AM_SEND (__PYX_LIMITED_VERSION_HEX >= 0x030A0000)
  #endif
  #undef CYTHON_USE_DICT_VERSIONS
  #define CYTHON_USE_DICT_VERSIONS 0
  #undef CYTHON_USE_EXC_INFO_STACK
  #define CYTHON_USE_EXC_INFO_STACK 0
  #ifndef CYTHON_UPDATE_DESCRIPTOR_DOC
    #define CYTHON_UPDATE_DESCRIPTOR_DOC 0
  #endif
  #undef CYTHON_USE_FREELISTS
  #define CYTHON_USE_FREELISTS 0
#else
  #define CYTHON_COMPILING_IN_PYPY 0
  #define CYTHON_COMPILING_IN_CPYTHON 1
  #define CYTHON_COMPILING_IN_LIMITED_API 0
  #define CYTHON_COMPILING_IN_GRAAL 0
  #ifdef Py_GIL_DISABLED
    #define CYTHON_COMPILING_IN_CPYTHON_FREETHREADING 1
  #else
    #define CYTHON_COMPILING_IN_CPYTHON_FREETHREADING 0
  #endif
  #if PY_VERSION_HEX < 0x030A0000
    #undef CYTHON_USE_TYPE_SLOTS
    #define CYTHON_USE_TYPE_SLOTS 1
  #elif !defined(CYTHON_USE_TYPE_SLOTS)
    #define CYTHON_USE_TYPE_SLOTS 1
  #endif
  #ifndef CYTHON_USE_TYPE_SPECS
    #define CYTHON_USE_TYPE_SPECS 0
  #endif
  #ifndef CYTHON_USE_PYTYPE_LOOKUP
    #define CYTHON_USE_PYTYPE_LOOKUP 1
  #endif
  #ifndef CYTHON_USE_PYLONG_INTERNALS
    #define CYTHON_USE_PYLONG_INTERNALS 1
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    #undef CYTHON_USE_PYLIST_INTERNALS
    #define CYTHON_USE_PYLIST_INTERNALS 0
  #elif !defined(CYTHON_USE_PYLIST_INTERNALS)
    #define CYTHON_USE_PYLIST_INTERNALS 1
  #endif
  #ifndef CYTHON_USE_UNICODE_INTERNALS
    #define CYTHON_USE_UNICODE_INTERNALS 1
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING || PY_VERSION_HEX >= 0x030B00A2
    #undef CYTHON_USE_UNICODE_WRITER
    #define CYTHON_USE_UNICODE_WRITER 0
  #elif !defined(CYTHON_USE_UNICODE_WRITER)
    #define CYTHON_USE_UNICODE_WRITER 1
  #endif
  #ifndef CYTHON_AVOID_BORROWED_REFS
    #define CYTHON_AVOID_BORROWED_REFS 0
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    #undef CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
    #define CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS 1
  #elif !defined(CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS)
    #define CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS 0
  #endif
  #ifndef CYTHON_ASSUME_SAFE_MACROS
    #define CYTHON_ASSUME_SAFE_MACROS 1
  #endif
  #ifndef CYTHON_ASSUME_SAFE_SIZE
    #define CYTHON_ASSUME_SAFE_SIZE 1
  #endif
  #ifndef CYTHON_UNPACK_METHODS
    #define CYTHON_UNPACK_METHODS 1
  #endif
  #ifndef CYTHON_FAST_THREAD_STATE
    #define CYTHON_FAST_THREAD_STATE 1
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    #undef CYTHON_FAST_GIL
    #define CYTHON_FAST_GIL 0
  #elif !defined(CYTHON_FAST_GIL)
    #define CYTHON_FAST_GIL (PY_VERSION_HEX < 0x030C00A6)
  #endif
  #ifndef CYTHON_METH_FASTCALL
    #define CYTHON_METH_FASTCALL 1
  #endif
  #ifndef CYTHON_FAST_PYCALL
    #define CYTHON_FAST_PYCALL 1
  #endif
  #ifndef CYTHON_PEP487_INIT_SUBCLASS
    #define CYTHON_PEP487_INIT_SUBCLASS 1
  #endif
  #ifndef CYTHON_PEP489_MULTI_PHASE_INIT
    #define CYTHON_PEP489_MULTI_PHASE_INIT 1
  #endif
  #ifndef CYTHON_USE_MODULE_STATE
    #define CYTHON_USE_MODULE_STATE 0
  #endif
  #ifndef CYTHON_USE_SYS_MONITORING
    #define CYTHON_USE_SYS_MONITORING (PY_VERSION_HEX >= 0x030d00B1)
  #endif
  #ifndef CYTHON_USE_TP_FINALIZE
    #define CYTHON_USE_TP_FINALIZE 1
  #endif
  #ifndef CYTHON_USE_AM_SEND
    #define CYTHON_USE_AM_SEND 1
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    #undef CYTHON_USE_DICT_VERSIONS
    #define CYTHON_USE_DICT_VERSIONS 0
  #elif !defined(CYTHON_USE_DICT_VERSIONS)
    #define CYTHON_USE_DICT_VERSIONS  (PY_VERSION_HEX < 0x030C00A5 && !CYTHON_USE_MODULE_STATE)
  #endif
  #ifndef CYTHON_USE_EXC_INFO_STACK
    #define CYTHON_USE_EXC_INFO_STACK 1
  #endif
  #ifndef CYTHON_UPDATE_DESCRIPTOR_DOC
    #define CYTHON_UPDATE_DESCRIPTOR_DOC 1
  #endif
  #ifndef CYTHON_USE_FREELISTS
    #define CYTHON_USE_FREELISTS (!CYTHON_COMPILING_IN_CPYTHON_FREETHREADING)
  #endif
#endif
#ifndef CYTHON_FAST_PYCCALL
#define CYTHON_FAST_PYCCALL  CYTHON_FAST_PYCALL
#endif
#ifndef CYTHON_VECTORCALL
#if CYTHON_COMPILING_IN_LIMITED_API
#define CYTHON_VECTORCALL  (__PYX_LIMITED_VERSION_HEX >= 0x030C0000)
#else
#define CYTHON_VECTORCALL  (CYTHON_FAST_PYCCALL && PY_VERSION_HEX >= 0x030800B1)
#endif
#endif
#define CYTHON_BACKPORT_VECTORCALL (CYTHON_METH_FASTCALL && PY_VERSION_HEX < 0x030800B1)
#if CYTHON_USE_PYLONG_INTERNALS
  #undef SHIFT
  #undef BASE
  #undef MASK
  #ifdef SIZEOF_VOID_P
    enum { __pyx_check_sizeof_voidp = 1 / (int)(SIZEOF_VOID_P == sizeof(void*)) };
  #endif
#endif
#ifndef __has_attribute
  #define __has_attribute(x) 0
#endif
#ifndef __has_cpp_attribute
  #define __has_cpp_attribute(x) 0
#endif
#ifndef CYTHON_RESTRICT
  #if defined(__GNUC__)
    #define CYTHON_RESTRICT __restrict__
  #elif defined(_MSC_VER) && _MSC_VER >= 1400
    #define CYTHON_RESTRICT __restrict
  #elif defined (__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
    #define CYTHON_RESTRICT restrict
  #else
    #define CYTHON_RESTRICT
  #endif
#endif
#ifndef CYTHON_UNUSED
  #if defined(__cplusplus)
    /* for clang __has_cpp_attribute(maybe_unused) is true even before C++17
     * but leads to warnings with -pedantic, since it is a C++17 feature */
    #if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
      #if __has_cpp_attribute(maybe_unused)
        #define CYTHON_UNUSED [[maybe_unused]]
      #endif
    #endif
  #endif
#endif
#ifndef CYTHON_UNUSED
# if defined(__GNUC__)
#   if !(defined(__cplusplus)) || (__GNUC__ > 3 || (__GNUC__ == 3 && __GNUC_MINOR__ >= 4))
#     define CYTHON_UNUSED __attribute__ ((__unused__))
#   else
#     define CYTHON_UNUSED
#   endif
# elif defined(__ICC) || (defined(__INTEL_COMPILER) && !defined(_MSC_VER))
#   define CYTHON_UNUSED __attribute__ ((__unused__))
# else
#   define CYTHON_UNUSED
# endif
#endif
#ifndef CYTHON_UNUSED_VAR
#  if defined(__cplusplus)
     template<class T> void CYTHON_UNUSED_VAR( const T& ) { }
#  else
#    define CYTHON_UNUSED_VAR(x) (void)(x)
#  endif
#endif
#ifndef CYTHON_MAYBE_UNUSED_VAR
  #define CYTHON_MAYBE_UNUSED_VAR(x) CYTHON_UNUSED_VAR(x)
#endif
#ifndef CYTHON_NCP_UNUSED
# if CYTHON_COMPILING_IN_CPYTHON && !CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
#  define CYTHON_NCP_UNUSED
# else
#  define CYTHON_NCP_UNUSED CYTHON_UNUSED
# endif
#endif
#ifndef CYTHON_USE_CPP_STD_MOVE
  #if defined(__cplusplus) && (\
    __cplusplus >= 201103L || (defined(_MSC_VER) && _MSC_VER >= 1600))
    #define CYTHON_USE_CPP_STD_MOVE 1
  #else
    #define CYTHON_USE_CPP_STD_MOVE 0
  #endif
#endif
#define __Pyx_void_to_None(void_result) ((void)(void_result), Py_INCREF(Py_None), Py_None)
#ifdef _MSC_VER
    #ifndef _MSC_STDINT_H_
        #if _MSC_VER < 1300
            typedef unsigned char     uint8_t;
            typedef unsigned short    uint16_t;
            typedef unsigned int      uint32_t;
        #else
            typedef unsigned __int8   uint8_t;
            typedef unsigned __int16  uint16_t;
            typedef unsigned __int32  uint32_t;
        #endif
    #endif
    #if _MSC_VER < 1300
        #ifdef _WIN64
            typedef unsigned long long  __pyx_uintptr_t;
        #else
            typedef unsigned int        __pyx_uintptr_t;
        #endif
    #else
        #ifdef _WIN64
            typedef unsigned __int64    __pyx_uintptr_t;
        #else
            typedef unsigned __int32    __pyx_uintptr_t;
        #endif
    #endif
#else
    #include <stdint.h>
    typedef uintptr_t  __pyx_uintptr_t;
#endif
#ifndef CYTHON_FALLTHROUGH
  #if defined(__cplusplus)
    /* for clang __has_cpp_attribute(fallthrough) is true even before C++17
     * but leads to warnings with -pedantic, since it is a C++17 feature */
    #if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
      #if __has_cpp_attribute(fallthrough)
        #define CYTHON_FALLTHROUGH [[fallthrough]]
      #endif
    #endif
    #ifndef CYTHON_FALLTHROUGH
      #if __has_cpp_attribute(clang::fallthrough)
        #define CYTHON_FALLTHROUGH [[clang::fallthrough]]
      #elif __has_cpp_attribute(gnu::fallthrough)
        #define CYTHON_FALLTHROUGH [[gnu::fallthrough]]
      #endif
    #endif
  #endif
  #ifndef CYTHON_FALLTHROUGH
    #if __has_attribute(fallthrough)
      #define CYTHON_FALLTHROUGH __attribute__((fallthrough))
    #else
      #define CYTHON_FALLTHROUGH
    #endif
  #endif
  #if defined(__clang__) && defined(__apple_build_version__)
    #if __apple_build_version__ < 7000000
      #undef  CYTHON_FALLTHROUGH
      #define CYTHON_FALLTHROUGH
    #endif
  #endif
#endif
#ifndef Py_UNREACHABLE
  #define Py_UNREACHABLE()  assert(0); abort()
#endif
#ifdef __cplusplus
  template <typename T>
  struct __PYX_IS_UNSIGNED_IMPL {static const bool value = T(0) < T(-1);};
  #define __PYX_IS_UNSIGNED(type) (__PYX_IS_UNSIGNED_IMPL<type>::value)
#else
  #define __PYX_IS_UNSIGNED(type) (((type)-1) > 0)
#endif
#if CYTHON_COMPILING_IN_PYPY == 1
  #define __PYX_NEED_TP_PRINT_SLOT  (PY_VERSION_HEX >= 0x030800b4 && PY_VERSION_HEX < 0x030A0000)
#else
  #define __PYX_NEED_TP_PRINT_SLOT  (PY_VERSION_HEX >= 0x030800b4 && PY_VERSION_HEX < 0x03090000)
#endif
#define __PYX_REINTERPRET_FUNCION(func_pointer, other_pointer) ((func_pointer)(void(*)(void))(other_pointer))

/* CInitCode */
#ifndef CYTHON_INLINE
  #if defined(__clang__)
    #define CYTHON_INLINE __inline__ __attribute__ ((__unused__))
  #elif defined(__GNUC__)
    #define CYTHON_INLINE __inline__
  #elif defined(_MSC_VER)
    #define CYTHON_INLINE __inline
  #elif defined (__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
    #define CYTHON_INLINE inline
  #else
    #define CYTHON_INLINE
  #endif
#endif

/* PythonCompatibility */
#define __PYX_BUILD_PY_SSIZE_T "n"
#define CYTHON_FORMAT_SSIZE_T "z"
#define __Pyx_BUILTIN_MODULE_NAME "builtins"
#define __Pyx_DefaultClassType PyType_Type
#if CYTHON_COMPILING_IN_LIMITED_API
    #ifndef CO_OPTIMIZED
    static int CO_OPTIMIZED;
    #endif
    #ifndef CO_NEWLOCALS
    static int CO_NEWLOCALS;
    #endif
    #ifndef CO_VARARGS
    static int CO_VARARGS;
    #endif
    #ifndef CO_VARKEYWORDS
    static int CO_VARKEYWORDS;
    #endif
    #ifndef CO_ASYNC_GENERATOR
    static int CO_ASYNC_GENERATOR;
    #endif
    #ifndef CO_GENERATOR
    static int CO_GENERATOR;
    #endif
    #ifndef CO_COROUTINE
    static int CO_COROUTINE;
    #endif
#else
    #ifndef CO_COROUTINE
      #define CO_COROUTINE 0x80
    #endif
    #ifndef CO_ASYNC_GENERATOR
      #define CO_ASYNC_GENERATOR 0x200
    #endif
#endif
static int __Pyx_init_co_variables(void);
#if PY_VERSION_HEX >= 0x030900A4 || defined(Py_IS_TYPE)
  #define __Pyx_IS_TYPE(ob, type) Py_IS_TYPE(ob, type)
#else
  #define __Pyx_IS_TYPE(ob, type) (((const PyObject*)ob)->ob_type == (type))
#endif
#if PY_VERSION_HEX >= 0x030A00B1 || defined(Py_Is)
  #define __Pyx_Py_Is(x, y)  Py_Is(x, y)
#else
  #define __Pyx_Py_Is(x, y) ((x) == (y))
#endif
#if PY_VERSION_HEX >= 0x030A00B1 || defined(Py_IsNone)
  #define __Pyx_Py_IsNone(ob) Py_IsNone(ob)
#else
  #define __Pyx_Py_IsNone(ob) __Pyx_Py_Is((ob), Py_None)
#endif
#if PY_VERSION_HEX >= 0x030A00B1 || defined(Py_IsTrue)
  #define __Pyx_Py_IsTrue(ob) Py_IsTrue(ob)
#else
  #define __Pyx_Py_IsTrue(ob) __Pyx_Py_Is((ob), Py_True)
#endif
#if PY_VERSION_HEX >= 0x030A00B1 || defined(Py_IsFalse)
  #define __Pyx_Py_IsFalse(ob) Py_IsFalse(ob)
#else
  #define __Pyx_Py_IsFalse(ob) __Pyx_Py_Is((ob), Py_False)
#endif
#define __Pyx_NoneAsNull(obj)  (__Pyx_Py_IsNone(obj) ? NULL : (obj))
#if PY_VERSION_HEX >= 0x030900F0 && !CYTHON_COMPILING_IN_PYPY
  #define __Pyx_PyObject_GC_IsFinalized(o) PyObject_GC_IsFinalized(o)
#else
  #define __Pyx_PyObject_GC_IsFinalized(o) _PyGC_FINALIZED(o)
#endif
#ifndef Py_TPFLAGS_CHECKTYPES
  #define Py_TPFLAGS_CHECKTYPES 0
#endif
#ifndef Py_TPFLAGS_HAVE_INDEX
  #define Py_TPFLAGS_HAVE_INDEX 0
#endif
#ifndef Py_TPFLAGS_HAVE_NEWBUFFER
  #define Py_TPFLAGS_HAVE_NEWBUFFER 0
#endif
#ifndef Py_TPFLAGS_HAVE_FINALIZE
  #define Py_TPFLAGS_HAVE_FINALIZE 0
#endif
#ifndef Py_TPFLAGS_SEQUENCE
  #define Py_TPFLAGS_SEQUENCE 0
#endif
#ifndef Py_TPFLAGS_MAPPING
  #define Py_TPFLAGS_MAPPING 0
#endif
#ifndef METH_STACKLESS
  #define METH_STACKLESS 0
#endif
#ifndef METH_FASTCALL
  #ifndef METH_FASTCALL
     #define METH_FASTCALL 0x80
  #endif
  typedef PyObject *(*__Pyx_PyCFunctionFast) (PyObject *self, PyObject *const *args, Py_ssize_t nargs);
  typedef PyObject *(*__Pyx_PyCFunctionFastWithKeywords) (PyObject *self, PyObject *const *args,
                                                          Py_ssize_t nargs, PyObject *kwnames);
#else
  #if PY_VERSION_HEX >= 0x030d00A4
  #  define __Pyx_PyCFunctionFast PyCFunctionFast
  #  define __Pyx_PyCFunctionFastWithKeywords PyCFunctionFastWithKeywords
  #else
  #  define __Pyx_PyCFunctionFast _PyCFunctionFast
  #  define __Pyx_PyCFunctionFastWithKeywords _PyCFunctionFastWithKeywords
  #endif
#endif
#if CYTHON_METH_FASTCALL
  #define __Pyx_METH_FASTCALL METH_FASTCALL
  #define __Pyx_PyCFunction_FastCall __Pyx_PyCFunctionFast
  #define __Pyx_PyCFunction_FastCallWithKeywords __Pyx_PyCFunctionFastWithKeywords
#else
  #define __Pyx_METH_FASTCALL METH_VARARGS
  #define __Pyx_PyCFunction_FastCall PyCFunction
  #define __Pyx_PyCFunction_FastCallWithKeywords PyCFunctionWithKeywords
#endif
#if CYTHON_VECTORCALL
  #define __pyx_vectorcallfunc vectorcallfunc
  #define __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET  PY_VECTORCALL_ARGUMENTS_OFFSET
  #define __Pyx_PyVectorcall_NARGS(n)  PyVectorcall_NARGS((size_t)(n))
#elif CYTHON_BACKPORT_VECTORCALL
  typedef PyObject *(*__pyx_vectorcallfunc)(PyObject *callable, PyObject *const *args,
                                            size_t nargsf, PyObject *kwnames);
  #define __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET  ((size_t)1 << (8 * sizeof(size_t) - 1))
  #define __Pyx_PyVectorcall_NARGS(n)  ((Py_ssize_t)(((size_t)(n)) & ~__Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET))
#else
  #define __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET  0
  #define __Pyx_PyVectorcall_NARGS(n)  ((Py_ssize_t)(n))
#endif
#if PY_VERSION_HEX >= 0x030900B1
#define __Pyx_PyCFunction_CheckExact(func)  PyCFunction_CheckExact(func)
#else
#define __Pyx_PyCFunction_CheckExact(func)  PyCFunction_Check(func)
#endif
#define __Pyx_CyOrPyCFunction_Check(func)  PyCFunction_Check(func)
#if CYTHON_COMPILING_IN_CPYTHON
#define __Pyx_CyOrPyCFunction_GET_FUNCTION(func)  (((PyCFunctionObject*)(func))->m_ml->ml_meth)
#elif !CYTHON_COMPILING_IN_LIMITED_API
#define __Pyx_CyOrPyCFunction_GET_FUNCTION(func)  PyCFunction_GET_FUNCTION(func)
#endif
#if CYTHON_COMPILING_IN_CPYTHON
#define __Pyx_CyOrPyCFunction_GET_FLAGS(func)  (((PyCFunctionObject*)(func))->m_ml->ml_flags)
static CYTHON_INLINE PyObject* __Pyx_CyOrPyCFunction_GET_SELF(PyObject *func) {
    return (__Pyx_CyOrPyCFunction_GET_FLAGS(func) & METH_STATIC) ? NULL : ((PyCFunctionObject*)func)->m_self;
}
#endif
static CYTHON_INLINE int __Pyx__IsSameCFunction(PyObject *func, void (*cfunc)(void)) {
#if CYTHON_COMPILING_IN_LIMITED_API
    return PyCFunction_Check(func) && PyCFunction_GetFunction(func) == (PyCFunction) cfunc;
#else
    return PyCFunction_Check(func) && PyCFunction_GET_FUNCTION(func) == (PyCFunction) cfunc;
#endif
}
#define __Pyx_IsSameCFunction(func, cfunc)   __Pyx__IsSameCFunction(func, cfunc)
#if __PYX_LIMITED_VERSION_HEX < 0x03090000
  #define __Pyx_PyType_FromModuleAndSpec(m, s, b)  ((void)m, PyType_FromSpecWithBases(s, b))
  typedef PyObject *(*__Pyx_PyCMethod)(PyObject *, PyTypeObject *, PyObject *const *, size_t, PyObject *);
#else
  #define __Pyx_PyType_FromModuleAndSpec(m, s, b)  PyType_FromModuleAndSpec(m, s, b)
  #define __Pyx_PyCMethod  PyCMethod
#endif
#ifndef METH_METHOD
  #define METH_METHOD 0x200
#endif
#if CYTHON_COMPILING_IN_PYPY && !defined(PyObject_Malloc)
  #define PyObject_Malloc(s)   PyMem_Malloc(s)
  #define PyObject_Free(p)     PyMem_Free(p)
  #define PyObject_Realloc(p)  PyMem_Realloc(p)
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
  #define __Pyx_PyFrame_SetLineNumber(frame, lineno)
#elif CYTHON_COMPILING_IN_GRAAL
  #define __Pyx_PyCode_HasFreeVars(co)  (PyCode_GetNumFree(co) > 0)
  #define __Pyx_PyFrame_SetLineNumber(frame, lineno) _PyFrame_SetLineNumber((frame), (lineno))
#else
  #define __Pyx_PyCode_HasFreeVars(co)  (PyCode_GetNumFree(co) > 0)
  #define __Pyx_PyFrame_SetLineNumber(frame, lineno)  (frame)->f_lineno = (lineno)
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
  #define __Pyx_PyThreadState_Current PyThreadState_Get()
#elif !CYTHON_FAST_THREAD_STATE
  #define __Pyx_PyThreadState_Current PyThreadState_GET()
#elif PY_VERSION_HEX >= 0x030d00A1
  #define __Pyx_PyThreadState_Current PyThreadState_GetUnchecked()
#else
  #define __Pyx_PyThreadState_Current _PyThreadState_UncheckedGet()
#endif
#if CYTHON_USE_MODULE_STATE
static CYTHON_INLINE void *__Pyx__PyModule_GetState(PyObject *op)
{
    void *result;
    result = PyModule_GetState(op);
    if (!result)
        Py_FatalError("Couldn't find the module state");
    return result;
}
#define __Pyx_PyModule_GetState(o) (__pyx_mstatetype *)__Pyx__PyModule_GetState(o)
#else
#define __Pyx_PyModule_GetState(op) ((void)op,__pyx_mstate_global)
#endif
#define __Pyx_PyObject_GetSlot(obj, name, func_ctype)  __Pyx_PyType_GetSlot(Py_TYPE((PyObject *) obj), name, func_ctype)
#define __Pyx_PyObject_TryGetSlot(obj, name, func_ctype) __Pyx_PyType_TryGetSlot(Py_TYPE(obj), name, func_ctype)
#define __Pyx_PyObject_GetSubSlot(obj, sub, name, func_ctype) __Pyx_PyType_GetSubSlot(Py_TYPE(obj), sub, name, func_ctype)
#define __Pyx_PyObject_TryGetSubSlot(obj, sub, name, func_ctype) __Pyx_PyType_TryGetSubSlot(Py_TYPE(obj), sub, name, func_ctype)
#if CYTHON_USE_TYPE_SLOTS
  #define __Pyx_PyType_GetSlot(type, name, func_ctype)  ((type)->name)
  #define __Pyx_PyType_TryGetSlot(type, name, func_ctype) __Pyx_PyType_GetSlot(type, name, func_ctype)
  #define __Pyx_PyType_GetSubSlot(type, sub, name, func_ctype) (((type)->sub) ? ((type)->sub->name) : NULL)
  #define __Pyx_PyType_TryGetSubSlot(type, sub, name, func_ctype) __Pyx_PyType_GetSubSlot(type, sub, name, func_ctype)
#else
  #define __Pyx_PyType_GetSlot(type, name, func_ctype)  ((func_ctype) PyType_GetSlot((type), Py_##name))
  #define __Pyx_PyType_TryGetSlot(type, name, func_ctype)\
    ((__PYX_LIMITED_VERSION_HEX >= 0x030A0000 ||\
     (PyType_GetFlags(type) & Py_TPFLAGS_HEAPTYPE) || __Pyx_get_runtime_version() >= 0x030A0000) ?\
     __Pyx_PyType_GetSlot(type, name, func_ctype) : NULL)
  #define __Pyx_PyType_GetSubSlot(obj, sub, name, func_ctype) __Pyx_PyType_GetSlot(obj, name, func_ctype)
  #define __Pyx_PyType_TryGetSubSlot(obj, sub, name, func_ctype) __Pyx_PyType_TryGetSlot(obj, name, func_ctype)
#endif
#if CYTHON_COMPILING_IN_CPYTHON || defined(_PyDict_NewPresized)
#define __Pyx_PyDict_NewPresized(n)  ((n <= 8) ? PyDict_New() : _PyDict_NewPresized(n))
#else
#define __Pyx_PyDict_NewPresized(n)  PyDict_New()
#endif
#define __Pyx_PyNumber_Divide(x,y)         PyNumber_TrueDivide(x,y)
#define __Pyx_PyNumber_InPlaceDivide(x,y)  PyNumber_InPlaceTrueDivide(x,y)
#if CYTHON_COMPILING_IN_CPYTHON && CYTHON_USE_UNICODE_INTERNALS
#define __Pyx_PyDict_GetItemStrWithError(dict, name)  _PyDict_GetItem_KnownHash(dict, name, ((PyASCIIObject *) name)->hash)
static CYTHON_INLINE PyObject * __Pyx_PyDict_GetItemStr(PyObject *dict, PyObject *name) {
    PyObject *res = __Pyx_PyDict_GetItemStrWithError(dict, name);
    if (res == NULL) PyErr_Clear();
    return res;
}
#elif !CYTHON_COMPILING_IN_PYPY || PYPY_VERSION_NUM >= 0x07020000
#define __Pyx_PyDict_GetItemStrWithError  PyDict_GetItemWithError
#define __Pyx_PyDict_GetItemStr           PyDict_GetItem
#else
static CYTHON_INLINE PyObject * __Pyx_PyDict_GetItemStrWithError(PyObject *dict, PyObject *name) {
#if CYTHON_COMPILING_IN_PYPY
    return PyDict_GetItem(dict, name);
#else
    PyDictEntry *ep;
    PyDictObject *mp = (PyDictObject*) dict;
    long hash = ((PyStringObject *) name)->ob_shash;
    assert(hash != -1);
    ep = (mp->ma_lookup)(mp, name, hash);
    if (ep == NULL) {
        return NULL;
    }
    return ep->me_value;
#endif
}
#define __Pyx_PyDict_GetItemStr           PyDict_GetItem
#endif
#if CYTHON_USE_TYPE_SLOTS
  #define __Pyx_PyType_GetFlags(tp)   (((PyTypeObject *)tp)->tp_flags)
  #define __Pyx_PyType_HasFeature(type, feature)  ((__Pyx_PyType_GetFlags(type) & (feature)) != 0)
#else
  #define __Pyx_PyType_GetFlags(tp)   (PyType_GetFlags((PyTypeObject *)tp))
  #define __Pyx_PyType_HasFeature(type, feature)  PyType_HasFeature(type, feature)
#endif
#define __Pyx_PyObject_GetIterNextFunc(iterator)  __Pyx_PyObject_GetSlot(iterator, tp_iternext, iternextfunc)
#if CYTHON_USE_TYPE_SPECS && PY_VERSION_HEX >= 0x03080000
#define __Pyx_PyHeapTypeObject_GC_Del(obj)  {\
    PyTypeObject *type = Py_TYPE((PyObject*)obj);\
    assert(__Pyx_PyType_HasFeature(type, Py_TPFLAGS_HEAPTYPE));\
    PyObject_GC_Del(obj);\
    Py_DECREF(type);\
}
#else
#define __Pyx_PyHeapTypeObject_GC_Del(obj)  PyObject_GC_Del(obj)
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
  #define __Pyx_PyUnicode_READY(op)       (0)
  #define __Pyx_PyUnicode_READ_CHAR(u, i) PyUnicode_ReadChar(u, i)
  #define __Pyx_PyUnicode_MAX_CHAR_VALUE(u)   ((void)u, 1114111U)
  #define __Pyx_PyUnicode_KIND(u)         ((void)u, (0))
  #define __Pyx_PyUnicode_DATA(u)         ((void*)u)
  #define __Pyx_PyUnicode_READ(k, d, i)   ((void)k, PyUnicode_ReadChar((PyObject*)(d), i))
  #define __Pyx_PyUnicode_IS_TRUE(u)      (0 != PyUnicode_GetLength(u))
#else
  #if PY_VERSION_HEX >= 0x030C0000
    #define __Pyx_PyUnicode_READY(op)       (0)
  #else
    #define __Pyx_PyUnicode_READY(op)       (likely(PyUnicode_IS_READY(op)) ?\
                                                0 : _PyUnicode_Ready((PyObject *)(op)))
  #endif
  #define __Pyx_PyUnicode_READ_CHAR(u, i) PyUnicode_READ_CHAR(u, i)
  #define __Pyx_PyUnicode_MAX_CHAR_VALUE(u)   PyUnicode_MAX_CHAR_VALUE(u)
  #define __Pyx_PyUnicode_KIND(u)         ((int)PyUnicode_KIND(u))
  #define __Pyx_PyUnicode_DATA(u)         PyUnicode_DATA(u)
  #define __Pyx_PyUnicode_READ(k, d, i)   PyUnicode_READ(k, d, i)
  #define __Pyx_PyUnicode_WRITE(k, d, i, ch)  PyUnicode_WRITE(k, d, i, (Py_UCS4) ch)
  #if PY_VERSION_HEX >= 0x030C0000
    #define __Pyx_PyUnicode_IS_TRUE(u)      (0 != PyUnicode_GET_LENGTH(u))
  #else
    #if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x03090000
    #define __Pyx_PyUnicode_IS_TRUE(u)      (0 != (likely(PyUnicode_IS_READY(u)) ? PyUnicode_GET_LENGTH(u) : ((PyCompactUnicodeObject *)(u))->wstr_length))
    #else
    #define __Pyx_PyUnicode_IS_TRUE(u)      (0 != (likely(PyUnicode_IS_READY(u)) ? PyUnicode_GET_LENGTH(u) : PyUnicode_GET_SIZE(u)))
    #endif
  #endif
#endif
#if CYTHON_COMPILING_IN_PYPY
  #define __Pyx_PyUnicode_Concat(a, b)      PyNumber_Add(a, b)
  #define __Pyx_PyUnicode_ConcatSafe(a, b)  PyNumber_Add(a, b)
#else
  #define __Pyx_PyUnicode_Concat(a, b)      PyUnicode_Concat(a, b)
  #define __Pyx_PyUnicode_ConcatSafe(a, b)  ((unlikely((a) == Py_None) || unlikely((b) == Py_None)) ?\
      PyNumber_Add(a, b) : __Pyx_PyUnicode_Concat(a, b))
#endif
#if CYTHON_COMPILING_IN_PYPY
  #if !defined(PyUnicode_DecodeUnicodeEscape)
    #define PyUnicode_DecodeUnicodeEscape(s, size, errors)  PyUnicode_Decode(s, size, "unicode_escape", errors)
  #endif
  #if !defined(PyUnicode_Contains)
    #define PyUnicode_Contains(u, s)  PySequence_Contains(u, s)
  #endif
  #if !defined(PyByteArray_Check)
    #define PyByteArray_Check(obj)  PyObject_TypeCheck(obj, &PyByteArray_Type)
  #endif
  #if !defined(PyObject_Format)
    #define PyObject_Format(obj, fmt)  PyObject_CallMethod(obj, "__format__", "O", fmt)
  #endif
#endif
#define __Pyx_PyUnicode_FormatSafe(a, b)  ((unlikely((a) == Py_None || (PyUnicode_Check(b) && !PyUnicode_CheckExact(b)))) ? PyNumber_Remainder(a, b) : PyUnicode_Format(a, b))
#if CYTHON_COMPILING_IN_CPYTHON
  #define __Pyx_PySequence_ListKeepNew(obj)\
    (likely(PyList_CheckExact(obj) && Py_REFCNT(obj) == 1) ? __Pyx_NewRef(obj) : PySequence_List(obj))
#else
  #define __Pyx_PySequence_ListKeepNew(obj)  PySequence_List(obj)
#endif
#ifndef PySet_CheckExact
  #define PySet_CheckExact(obj)        __Pyx_IS_TYPE(obj, &PySet_Type)
#endif
#if PY_VERSION_HEX >= 0x030900A4
  #define __Pyx_SET_REFCNT(obj, refcnt) Py_SET_REFCNT(obj, refcnt)
  #define __Pyx_SET_SIZE(obj, size) Py_SET_SIZE(obj, size)
#else
  #define __Pyx_SET_REFCNT(obj, refcnt) Py_REFCNT(obj) = (refcnt)
  #define __Pyx_SET_SIZE(obj, size) Py_SIZE(obj) = (size)
#endif
#if CYTHON_AVOID_BORROWED_REFS || CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
  #if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
    #define __Pyx_PyList_GetItemRef(o, i) PyList_GetItemRef(o, i)
  #elif CYTHON_COMPILING_IN_LIMITED_API || !CYTHON_ASSUME_SAFE_MACROS
    #define __Pyx_PyList_GetItemRef(o, i) (likely((i) >= 0) ? PySequence_GetItem(o, i) : (PyErr_SetString(PyExc_IndexError, "list index out of range"), (PyObject*)NULL))
  #else
    #define __Pyx_PyList_GetItemRef(o, i) PySequence_ITEM(o, i)
  #endif
#elif CYTHON_COMPILING_IN_LIMITED_API || !CYTHON_ASSUME_SAFE_MACROS
  #if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
    #define __Pyx_PyList_GetItemRef(o, i) PyList_GetItemRef(o, i)
  #else
    #define __Pyx_PyList_GetItemRef(o, i) __Pyx_XNewRef(PyList_GetItem(o, i))
  #endif
#else
  #define __Pyx_PyList_GetItemRef(o, i) __Pyx_NewRef(PyList_GET_ITEM(o, i))
#endif
#if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
#define __Pyx_PyDict_GetItemRef(dict, key, result) PyDict_GetItemRef(dict, key, result)
#elif CYTHON_AVOID_BORROWED_REFS || CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
static CYTHON_INLINE int __Pyx_PyDict_GetItemRef(PyObject *dict, PyObject *key, PyObject **result) {
  *result = PyObject_GetItem(dict, key);
  if (*result == NULL) {
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
      PyErr_Clear();
      return 0;
    }
    return -1;
  }
  return 1;
}
#else
static CYTHON_INLINE int __Pyx_PyDict_GetItemRef(PyObject *dict, PyObject *key, PyObject **result) {
  *result = PyDict_GetItemWithError(dict, key);
  if (*result == NULL) {
    return PyErr_Occurred() ? -1 : 0;
  }
  Py_INCREF(*result);
  return 1;
}
#endif
#if defined(CYTHON_DEBUG_VISIT_CONST) && CYTHON_DEBUG_VISIT_CONST
  #define __Pyx_VISIT_CONST(obj)  Py_VISIT(obj)
#else
  #define __Pyx_VISIT_CONST(obj)
#endif
#if CYTHON_ASSUME_SAFE_MACROS
  #define __Pyx_PySequence_ITEM(o, i) PySequence_ITEM(o, i)
  #define __Pyx_PySequence_SIZE(seq)  Py_SIZE(seq)
  #define __Pyx_PyTuple_SET_ITEM(o, i, v) (PyTuple_SET_ITEM(o, i, v), (0))
  #define __Pyx_PyTuple_GET_ITEM(o, i) PyTuple_GET_ITEM(o, i)
  #define __Pyx_PyList_SET_ITEM(o, i, v) (PyList_SET_ITEM(o, i, v), (0))
  #define __Pyx_PyList_GET_ITEM(o, i) PyList_GET_ITEM(o, i)
#else
  #define __Pyx_PySequence_ITEM(o, i) PySequence_GetItem(o, i)
  #define __Pyx_PySequence_SIZE(seq)  PySequence_Size(seq)
  #define __Pyx_PyTuple_SET_ITEM(o, i, v) PyTuple_SetItem(o, i, v)
  #define __Pyx_PyTuple_GET_ITEM(o, i) PyTuple_GetItem(o, i)
  #define __Pyx_PyList_SET_ITEM(o, i, v) PyList_SetItem(o, i, v)
  #define __Pyx_PyList_GET_ITEM(o, i) PyList_GetItem(o, i)
#endif
#if CYTHON_ASSUME_SAFE_SIZE
  #define __Pyx_PyTuple_GET_SIZE(o) PyTuple_GET_SIZE(o)
  #define __Pyx_PyList_GET_SIZE(o) PyList_GET_SIZE(o)
  #define __Pyx_PySet_GET_SIZE(o) PySet_GET_SIZE(o)
  #define __Pyx_PyBytes_GET_SIZE(o) PyBytes_GET_SIZE(o)
  #define __Pyx_PyByteArray_GET_SIZE(o) PyByteArray_GET_SIZE(o)
  #define __Pyx_PyUnicode_GET_LENGTH(o) PyUnicode_GET_LENGTH(o)
#else
  #define __Pyx_PyTuple_GET_SIZE(o) PyTuple_Size(o)
  #define __Pyx_PyList_GET_SIZE(o) PyList_Size(o)
  #define __Pyx_PySet_GET_SIZE(o) PySet_Size(o)
  #define __Pyx_PyBytes_GET_SIZE(o) PyBytes_Size(o)
  #define __Pyx_PyByteArray_GET_SIZE(o) PyByteArray_Size(o)
  #define __Pyx_PyUnicode_GET_LENGTH(o) PyUnicode_GetLength(o)
#endif
#if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
  #define __Pyx_PyImport_AddModuleRef(name) PyImport_AddModuleRef(name)
#else
  static CYTHON_INLINE PyObject *__Pyx_PyImport_AddModuleRef(const char *name) {
      PyObject *module = PyImport_AddModule(name);
      Py_XINCREF(module);
      return module;
  }
#endif
#if CYTHON_COMPILING_IN_PYPY && !defined(PyUnicode_InternFromString)
  #define PyUnicode_InternFromString(s) PyUnicode_FromString(s)
#endif
#define __Pyx_PyLong_FromHash_t PyLong_FromSsize_t
#define __Pyx_PyLong_AsHash_t   __Pyx_PyIndex_AsSsize_t
#if __PYX_LIMITED_VERSION_HEX >= 0x030A0000
    #define __Pyx_PySendResult PySendResult
#else
    typedef enum {
        PYGEN_RETURN = 0,
        PYGEN_ERROR = -1,
        PYGEN_NEXT = 1,
    } __Pyx_PySendResult;
#endif
#if CYTHON_COMPILING_IN_LIMITED_API || PY_VERSION_HEX < 0x030A00A3
  typedef __Pyx_PySendResult (*__Pyx_pyiter_sendfunc)(PyObject *iter, PyObject *value, PyObject **result);
#else
  #define __Pyx_pyiter_sendfunc sendfunc
#endif
#if !CYTHON_USE_AM_SEND
#define __PYX_HAS_PY_AM_SEND 0
#elif __PYX_LIMITED_VERSION_HEX >= 0x030A0000
#define __PYX_HAS_PY_AM_SEND 1
#else
#define __PYX_HAS_PY_AM_SEND 2  // our own backported implementation
#endif
#if __PYX_HAS_PY_AM_SEND < 2
    #define __Pyx_PyAsyncMethodsStruct PyAsyncMethods
#else
    typedef struct {
        unaryfunc am_await;
        unaryfunc am_aiter;
        unaryfunc am_anext;
        __Pyx_pyiter_sendfunc am_send;
    } __Pyx_PyAsyncMethodsStruct;
    #define __Pyx_SlotTpAsAsync(s) ((PyAsyncMethods*)(s))
#endif
#if CYTHON_USE_AM_SEND && PY_VERSION_HEX < 0x030A00F0
    #define __Pyx_TPFLAGS_HAVE_AM_SEND (1UL << 21)
#else
    #define __Pyx_TPFLAGS_HAVE_AM_SEND (0)
#endif
#if PY_VERSION_HEX >= 0x03090000
#define __Pyx_PyInterpreterState_Get() PyInterpreterState_Get()
#else
#define __Pyx_PyInterpreterState_Get() PyThreadState_Get()->interp
#endif
#if CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX < 0x030A0000
#ifdef __cplusplus
extern "C"
#endif
PyAPI_FUNC(void *) PyMem_Calloc(size_t nelem, size_t elsize);
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
static int __Pyx_init_co_variable(PyObject *inspect, const char* name, int *write_to) {
    int value;
    PyObject *py_value = PyObject_GetAttrString(inspect, name);
    if (!py_value) return 0;
    value = (int) PyLong_AsLong(py_value);
    Py_DECREF(py_value);
    *write_to = value;
    return value != -1 || !PyErr_Occurred();
}
static int __Pyx_init_co_variables(void) {
    PyObject *inspect;
    int result;
    inspect = PyImport_ImportModule("inspect");
    result =
#if !defined(CO_OPTIMIZED)
        __Pyx_init_co_variable(inspect, "CO_OPTIMIZED", &CO_OPTIMIZED) &&
#endif
#if !defined(CO_NEWLOCALS)
        __Pyx_init_co_variable(inspect, "CO_NEWLOCALS", &CO_NEWLOCALS) &&
#endif
#if !defined(CO_VARARGS)
        __Pyx_init_co_variable(inspect, "CO_VARARGS", &CO_VARARGS) &&
#endif
#if !defined(CO_VARKEYWORDS)
        __Pyx_init_co_variable(inspect, "CO_VARKEYWORDS", &CO_VARKEYWORDS) &&
#endif
#if !defined(CO_ASYNC_GENERATOR)
        __Pyx_init_co_variable(inspect, "CO_ASYNC_GENERATOR", &CO_ASYNC_GENERATOR) &&
#endif
#if !defined(CO_GENERATOR)
        __Pyx_init_co_variable(inspect, "CO_GENERATOR", &CO_GENERATOR) &&
#endif
#if !defined(CO_COROUTINE)
        __Pyx_init_co_variable(inspect, "CO_COROUTINE", &CO_COROUTINE) &&
#endif
        1;
    Py_DECREF(inspect);
    return result ? 0 : -1;
}
#else
static int __Pyx_init_co_variables(void) {
    return 0;  // It's a limited API-only feature
}
#endif

/* MathInitCode */
#if defined(_WIN32) || defined(WIN32) || defined(MS_WINDOWS)
  #ifndef _USE_MATH_DEFINES
    #define _USE_MATH_DEFINES
  #endif
#endif
#include <math.h>
#ifdef NAN
#define __PYX_NAN() ((float) NAN)
#else
static CYTHON_INLINE float __PYX_NAN() {
  float value;
  memset(&value, 0xFF, sizeof(value));
  return value;
}
#endif
#if defined(__CYGWIN__) && defined(_LDBL_EQ_DBL)
#define __Pyx_truncl trunc
#else
#define __Pyx_truncl truncl
#endif

#ifndef CYTHON_CLINE_IN_TRACEBACK_RUNTIME
#define CYTHON_CLINE_IN_TRACEBACK_RUNTIME 0
#endif
#ifndef CYTHON_CLINE_IN_TRACEBACK
#define CYTHON_CLINE_IN_TRACEBACK CYTHON_CLINE_IN_TRACEBACK_RUNTIME
#endif
#if CYTHON_CLINE_IN_TRACEBACK
#define __PYX_MARK_ERR_POS(f_index, lineno)  { __pyx_filename = __pyx_f[f_index]; (void) __pyx_filename; __pyx_lineno = lineno; (void) __pyx_lineno; __pyx_clineno = __LINE__; (void) __pyx_clineno; }
#else
#define __PYX_MARK_ERR_POS(f_index, lineno)  { __pyx_filename = __pyx_f[f_index]; (void) __pyx_filename; __pyx_lineno = lineno; (void) __pyx_lineno; (void) __pyx_clineno; }
#endif
#define __PYX_ERR(f_index, lineno, Ln_error) \
    { __PYX_MARK_ERR_POS(f_index, lineno) goto Ln_error; }

#ifdef CYTHON_EXTERN_C
    #undef __PYX_EXTERN_C
    #define __PYX_EXTERN_C CYTHON_EXTERN_C
#elif defined(__PYX_EXTERN_C)
    #ifdef _MSC_VER
    #pragma message ("Please do not define the '__PYX_EXTERN_C' macro externally. Use 'CYTHON_EXTERN_C' instead.")
    #else
    #warning Please do not define the '__PYX_EXTERN_C' macro externally. Use 'CYTHON_EXTERN_C' instead.
    #endif
#else
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

#define __PYX_HAVE__solver_c
#define __PYX_HAVE_API__solver_c
/* Early includes */
#ifdef _OPENMP
#include <omp.h>
#endif /* _OPENMP */

#if defined(PYREX_WITHOUT_ASSERTIONS) && !defined(CYTHON_WITHOUT_ASSERTIONS)
#define CYTHON_WITHOUT_ASSERTIONS
#endif

#define __PYX_DEFAULT_STRING_ENCODING_IS_ASCII 0
#define __PYX_DEFAULT_STRING_ENCODING_IS_UTF8 0
#define __PYX_DEFAULT_STRING_ENCODING ""
#define __Pyx_PyObject_FromString __Pyx_PyBytes_FromString
#define __Pyx_PyObject_FromStringAndSize __Pyx_PyBytes_FromStringAndSize
#define __Pyx_uchar_cast(c) ((unsigned char)c)
#define __Pyx_long_cast(x) ((long)x)
#define __Pyx_fits_Py_ssize_t(v, type, is_signed)  (\
    (sizeof(type) < sizeof(Py_ssize_t))  ||\
    (sizeof(type) > sizeof(Py_ssize_t) &&\
          likely(v < (type)PY_SSIZE_T_MAX ||\
                 v == (type)PY_SSIZE_T_MAX)  &&\
          (!is_signed || likely(v > (type)PY_SSIZE_T_MIN ||\
                                v == (type)PY_SSIZE_T_MIN)))  ||\
    (sizeof(type) == sizeof(Py_ssize_t) &&\
          (is_signed || likely(v < (type)PY_SSIZE_T_MAX ||\
                               v == (type)PY_SSIZE_T_MAX)))  )
static CYTHON_INLINE int __Pyx_is_valid_index(Py_ssize_t i, Py_ssize_t limit) {
    return (size_t) i < (size_t) limit;
}
#if defined (__cplusplus) && __cplusplus >= 201103L
    #include <cstdlib>
    #define __Pyx_sst_abs(value) std::abs(value)
#elif SIZEOF_INT >= SIZEOF_SIZE_T
    #define __Pyx_sst_abs(value) abs(value)
#elif SIZEOF_LONG >= SIZEOF_SIZE_T
    #define __Pyx_sst_abs(value) labs(value)
#elif defined (_MSC_VER)
    #define __Pyx_sst_abs(value) ((Py_ssize_t)_abs64(value))
#elif defined (__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
    #define __Pyx_sst_abs(value) llabs(value)
#elif defined (__GNUC__)
    #define __Pyx_sst_abs(value) __builtin_llabs(value)
#else
    #define __Pyx_sst_abs(value) ((value<0) ? -value : value)
#endif
static CYTHON_INLINE Py_ssize_t __Pyx_ssize_strlen(const char *s);
static CYTHON_INLINE const char* __Pyx_PyObject_AsString(PyObject*);
static CYTHON_INLINE const char* __Pyx_PyObject_AsStringAndSize(PyObject*, Py_ssize_t* length);
static CYTHON_INLINE PyObject* __Pyx_PyByteArray_FromString(const char*);
#define __Pyx_PyByteArray_FromStringAndSize(s, l) PyByteArray_FromStringAndSize((const char*)s, l)
#define __Pyx_PyBytes_FromString        PyBytes_FromString
#define __Pyx_PyBytes_FromStringAndSize PyBytes_FromStringAndSize
static CYTHON_INLINE PyObject* __Pyx_PyUnicode_FromString(const char*);
#if CYTHON_ASSUME_SAFE_MACROS
    #define __Pyx_PyBytes_AsWritableString(s)     ((char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyBytes_AsWritableSString(s)    ((signed char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyBytes_AsWritableUString(s)    ((unsigned char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyBytes_AsString(s)     ((const char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyBytes_AsSString(s)    ((const signed char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyBytes_AsUString(s)    ((const unsigned char*) PyBytes_AS_STRING(s))
    #define __Pyx_PyByteArray_AsString(s) PyByteArray_AS_STRING(s)
#else
    #define __Pyx_PyBytes_AsWritableString(s)     ((char*) PyBytes_AsString(s))
    #define __Pyx_PyBytes_AsWritableSString(s)    ((signed char*) PyBytes_AsString(s))
    #define __Pyx_PyBytes_AsWritableUString(s)    ((unsigned char*) PyBytes_AsString(s))
    #define __Pyx_PyBytes_AsString(s)     ((const char*) PyBytes_AsString(s))
    #define __Pyx_PyBytes_AsSString(s)    ((const signed char*) PyBytes_AsString(s))
    #define __Pyx_PyBytes_AsUString(s)    ((const unsigned char*) PyBytes_AsString(s))
    #define __Pyx_PyByteArray_AsString(s) PyByteArray_AsString(s)
#endif
#define __Pyx_PyObject_AsWritableString(s)    ((char*)(__pyx_uintptr_t) __Pyx_PyObject_AsString(s))
#define __Pyx_PyObject_AsWritableSString(s)    ((signed char*)(__pyx_uintptr_t) __Pyx_PyObject_AsString(s))
#define __Pyx_PyObject_AsWritableUString(s)    ((unsigned char*)(__pyx_uintptr_t) __Pyx_PyObject_AsString(s))
#define __Pyx_PyObject_AsSString(s)    ((const signed char*) __Pyx_PyObject_AsString(s))
#define __Pyx_PyObject_AsUString(s)    ((const unsigned char*) __Pyx_PyObject_AsString(s))
#define __Pyx_PyObject_FromCString(s)  __Pyx_PyObject_FromString((const char*)s)
#define __Pyx_PyBytes_FromCString(s)   __Pyx_PyBytes_FromString((const char*)s)
#define __Pyx_PyByteArray_FromCString(s)   __Pyx_PyByteArray_FromString((const char*)s)
#define __Pyx_PyUnicode_FromCString(s) __Pyx_PyUnicode_FromString((const char*)s)
#define __Pyx_PyUnicode_FromOrdinal(o)       PyUnicode_FromOrdinal((int)o)
#define __Pyx_PyUnicode_AsUnicode            PyUnicode_AsUnicode
static CYTHON_INLINE PyObject *__Pyx_NewRef(PyObject *obj) {
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x030a0000 || defined(Py_NewRef)
    return Py_NewRef(obj);
#else
    Py_INCREF(obj);
    return obj;
#endif
}
static CYTHON_INLINE PyObject *__Pyx_XNewRef(PyObject *obj) {
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x030a0000 || defined(Py_XNewRef)
    return Py_XNewRef(obj);
#else
    Py_XINCREF(obj);
    return obj;
#endif
}
static CYTHON_INLINE PyObject *__Pyx_Owned_Py_None(int b);
static CYTHON_INLINE PyObject * __Pyx_PyBool_FromLong(long b);
static CYTHON_INLINE int __Pyx_PyObject_IsTrue(PyObject*);
static CYTHON_INLINE int __Pyx_PyObject_IsTrueAndDecref(PyObject*);
static CYTHON_INLINE PyObject* __Pyx_PyNumber_Long(PyObject* x);
#define __Pyx_PySequence_Tuple(obj)\
    (likely(PyTuple_CheckExact(obj)) ? __Pyx_NewRef(obj) : PySequence_Tuple(obj))
static CYTHON_INLINE Py_ssize_t __Pyx_PyIndex_AsSsize_t(PyObject*);
static CYTHON_INLINE PyObject * __Pyx_PyLong_FromSize_t(size_t);
static CYTHON_INLINE Py_hash_t __Pyx_PyIndex_AsHash_t(PyObject*);
#if CYTHON_ASSUME_SAFE_MACROS
#define __Pyx_PyFloat_AsDouble(x) (PyFloat_CheckExact(x) ? PyFloat_AS_DOUBLE(x) : PyFloat_AsDouble(x))
#define __Pyx_PyFloat_AS_DOUBLE(x) PyFloat_AS_DOUBLE(x)
#else
#define __Pyx_PyFloat_AsDouble(x) PyFloat_AsDouble(x)
#define __Pyx_PyFloat_AS_DOUBLE(x) PyFloat_AsDouble(x)
#endif
#define __Pyx_PyFloat_AsFloat(x) ((float) __Pyx_PyFloat_AsDouble(x))
#define __Pyx_PyNumber_Int(x) (PyLong_CheckExact(x) ? __Pyx_NewRef(x) : PyNumber_Long(x))
#if CYTHON_USE_PYLONG_INTERNALS
  #if PY_VERSION_HEX >= 0x030C00A7
  #ifndef _PyLong_SIGN_MASK
    #define _PyLong_SIGN_MASK 3
  #endif
  #ifndef _PyLong_NON_SIZE_BITS
    #define _PyLong_NON_SIZE_BITS 3
  #endif
  #define __Pyx_PyLong_Sign(x)  (((PyLongObject*)x)->long_value.lv_tag & _PyLong_SIGN_MASK)
  #define __Pyx_PyLong_IsNeg(x)  ((__Pyx_PyLong_Sign(x) & 2) != 0)
  #define __Pyx_PyLong_IsNonNeg(x)  (!__Pyx_PyLong_IsNeg(x))
  #define __Pyx_PyLong_IsZero(x)  (__Pyx_PyLong_Sign(x) & 1)
  #define __Pyx_PyLong_IsPos(x)  (__Pyx_PyLong_Sign(x) == 0)
  #define __Pyx_PyLong_CompactValueUnsigned(x)  (__Pyx_PyLong_Digits(x)[0])
  #define __Pyx_PyLong_DigitCount(x)  ((Py_ssize_t) (((PyLongObject*)x)->long_value.lv_tag >> _PyLong_NON_SIZE_BITS))
  #define __Pyx_PyLong_SignedDigitCount(x)\
        ((1 - (Py_ssize_t) __Pyx_PyLong_Sign(x)) * __Pyx_PyLong_DigitCount(x))
  #if defined(PyUnstable_Long_IsCompact) && defined(PyUnstable_Long_CompactValue)
    #define __Pyx_PyLong_IsCompact(x)     PyUnstable_Long_IsCompact((PyLongObject*) x)
    #define __Pyx_PyLong_CompactValue(x)  PyUnstable_Long_CompactValue((PyLongObject*) x)
  #else
    #define __Pyx_PyLong_IsCompact(x)     (((PyLongObject*)x)->long_value.lv_tag < (2 << _PyLong_NON_SIZE_BITS))
    #define __Pyx_PyLong_CompactValue(x)  ((1 - (Py_ssize_t) __Pyx_PyLong_Sign(x)) * (Py_ssize_t) __Pyx_PyLong_Digits(x)[0])
  #endif
  typedef Py_ssize_t  __Pyx_compact_pylong;
  typedef size_t  __Pyx_compact_upylong;
  #else
  #define __Pyx_PyLong_IsNeg(x)  (Py_SIZE(x) < 0)
  #define __Pyx_PyLong_IsNonNeg(x)  (Py_SIZE(x) >= 0)
  #define __Pyx_PyLong_IsZero(x)  (Py_SIZE(x) == 0)
  #define __Pyx_PyLong_IsPos(x)  (Py_SIZE(x) > 0)
  #define __Pyx_PyLong_CompactValueUnsigned(x)  ((Py_SIZE(x) == 0) ? 0 : __Pyx_PyLong_Digits(x)[0])
  #define __Pyx_PyLong_DigitCount(x)  __Pyx_sst_abs(Py_SIZE(x))
  #define __Pyx_PyLong_SignedDigitCount(x)  Py_SIZE(x)
  #define __Pyx_PyLong_IsCompact(x)  (Py_SIZE(x) == 0 || Py_SIZE(x) == 1 || Py_SIZE(x) == -1)
  #define __Pyx_PyLong_CompactValue(x)\
        ((Py_SIZE(x) == 0) ? (sdigit) 0 : ((Py_SIZE(x) < 0) ? -(sdigit)__Pyx_PyLong_Digits(x)[0] : (sdigit)__Pyx_PyLong_Digits(x)[0]))
  typedef sdigit  __Pyx_compact_pylong;
  typedef digit  __Pyx_compact_upylong;
  #endif
  #if PY_VERSION_HEX >= 0x030C00A5
  #define __Pyx_PyLong_Digits(x)  (((PyLongObject*)x)->long_value.ob_digit)
  #else
  #define __Pyx_PyLong_Digits(x)  (((PyLongObject*)x)->ob_digit)
  #endif
#endif
#if __PYX_DEFAULT_STRING_ENCODING_IS_UTF8
  #define __Pyx_PyUnicode_FromStringAndSize(c_str, size) PyUnicode_DecodeUTF8(c_str, size, NULL)
#elif __PYX_DEFAULT_STRING_ENCODING_IS_ASCII
  #define __Pyx_PyUnicode_FromStringAndSize(c_str, size) PyUnicode_DecodeASCII(c_str, size, NULL)
#else
  #define __Pyx_PyUnicode_FromStringAndSize(c_str, size) PyUnicode_Decode(c_str, size, __PYX_DEFAULT_STRING_ENCODING, NULL)
#endif


/* Test for GCC > 2.95 */
#if defined(__GNUC__)     && (__GNUC__ > 2 || (__GNUC__ == 2 && (__GNUC_MINOR__ > 95)))
  #define likely(x)   __builtin_expect(!!(x), 1)
  #define unlikely(x) __builtin_expect(!!(x), 0)
#else /* !__GNUC__ or GCC < 2.95 */
  #define likely(x)   (x)
  #define unlikely(x) (x)
#endif /* __GNUC__ */
/* PretendToInitialize */
#ifdef __cplusplus
#if __cplusplus > 201103L
#include <type_traits>
#endif
template <typename T>
static void __Pyx_pretend_to_initialize(T* ptr) {
#if __cplusplus > 201103L
    if ((std::is_trivially_default_constructible<T>::value))
#endif
        *ptr = T();
    (void)ptr;
}
#else
static CYTHON_INLINE void __Pyx_pretend_to_initialize(void* ptr) { (void)ptr; }
#endif


#if !CYTHON_USE_MODULE_STATE
static PyObject *__pyx_m = NULL;
#endif
static int __pyx_lineno;
static int __pyx_clineno = 0;
static const char * const __pyx_cfilenm = __FILE__;
static const char *__pyx_filename;

/* #### Code section: filename_table ### */

static const char* const __pyx_f[] = {
  "solver_c.pyx",
};
/* #### Code section: utility_code_proto_before_types ### */
/* ForceInitThreads.proto */
#ifndef __PYX_FORCE_INIT_THREADS
  #define __PYX_FORCE_INIT_THREADS 0
#endif

/* NoFastGil.proto */
#define __Pyx_PyGILState_Ensure PyGILState_Ensure
#define __Pyx_PyGILState_Release PyGILState_Release
#define __Pyx_FastGIL_Remember()
#define __Pyx_FastGIL_Forget()
#define __Pyx_FastGilFuncInit()

/* Atomics.proto */
#include <pythread.h>
#ifndef CYTHON_ATOMICS
    #define CYTHON_ATOMICS 1
#endif
#define __PYX_CYTHON_ATOMICS_ENABLED() CYTHON_ATOMICS
#define __PYX_GET_CYTHON_COMPILING_IN_CPYTHON_FREETHREADING() CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
#define __pyx_atomic_int_type int
#define __pyx_nonatomic_int_type int
#if CYTHON_ATOMICS && (defined(__STDC_VERSION__) &&\
                        (__STDC_VERSION__ >= 201112L) &&\
                        !defined(__STDC_NO_ATOMICS__))
    #include <stdatomic.h>
#elif CYTHON_ATOMICS && (defined(__cplusplus) && (\
                    (__cplusplus >= 201103L) ||\
                    (defined(_MSC_VER) && _MSC_VER >= 1700)))
    #include <atomic>
#endif
#if CYTHON_ATOMICS && (defined(__STDC_VERSION__) &&\
                        (__STDC_VERSION__ >= 201112L) &&\
                        !defined(__STDC_NO_ATOMICS__) &&\
                       ATOMIC_INT_LOCK_FREE == 2)
    #undef __pyx_atomic_int_type
    #define __pyx_atomic_int_type atomic_int
    #define __pyx_atomic_ptr_type atomic_uintptr_t
    #define __pyx_nonatomic_ptr_type uintptr_t
    #define __pyx_atomic_incr_relaxed(value) atomic_fetch_add_explicit(value, 1, memory_order_relaxed)
    #define __pyx_atomic_incr_acq_rel(value) atomic_fetch_add_explicit(value, 1, memory_order_acq_rel)
    #define __pyx_atomic_decr_acq_rel(value) atomic_fetch_sub_explicit(value, 1, memory_order_acq_rel)
    #define __pyx_atomic_sub(value, arg) atomic_fetch_sub(value, arg)
    #define __pyx_atomic_int_cmp_exchange(value, expected, desired) atomic_compare_exchange_strong(value, expected, desired)
    #define __pyx_atomic_load(value) atomic_load(value)
    #define __pyx_atomic_store(value, new_value) atomic_store(value, new_value)
    #define __pyx_atomic_pointer_load_relaxed(value) atomic_load_explicit(value, memory_order_relaxed)
    #define __pyx_atomic_pointer_load_acquire(value) atomic_load_explicit(value, memory_order_acquire)
    #define __pyx_atomic_pointer_exchange(value, new_value) atomic_exchange(value, (__pyx_nonatomic_ptr_type)new_value)
    #if defined(__PYX_DEBUG_ATOMICS) && defined(_MSC_VER)
        #pragma message ("Using standard C atomics")
    #elif defined(__PYX_DEBUG_ATOMICS)
        #warning "Using standard C atomics"
    #endif
#elif CYTHON_ATOMICS && (defined(__cplusplus) && (\
                    (__cplusplus >= 201103L) ||\
\
                    (defined(_MSC_VER) && _MSC_VER >= 1700)) &&\
                    ATOMIC_INT_LOCK_FREE == 2)
    #undef __pyx_atomic_int_type
    #define __pyx_atomic_int_type std::atomic_int
    #define __pyx_atomic_ptr_type std::atomic_uintptr_t
    #define __pyx_nonatomic_ptr_type uintptr_t
    #define __pyx_atomic_incr_relaxed(value) std::atomic_fetch_add_explicit(value, 1, std::memory_order_relaxed)
    #define __pyx_atomic_incr_acq_rel(value) std::atomic_fetch_add_explicit(value, 1, std::memory_order_acq_rel)
    #define __pyx_atomic_decr_acq_rel(value) std::atomic_fetch_sub_explicit(value, 1, std::memory_order_acq_rel)
    #define __pyx_atomic_sub(value, arg) std::atomic_fetch_sub(value, arg)
    #define __pyx_atomic_int_cmp_exchange(value, expected, desired) std::atomic_compare_exchange_strong(value, expected, desired)
    #define __pyx_atomic_load(value) std::atomic_load(value)
    #define __pyx_atomic_store(value, new_value) std::atomic_store(value, new_value)
    #define __pyx_atomic_pointer_load_relaxed(value) std::atomic_load_explicit(value, std::memory_order_relaxed)
    #define __pyx_atomic_pointer_load_acquire(value) std::atomic_load_explicit(value, std::memory_order_acquire)
    #define __pyx_atomic_pointer_exchange(value, new_value) std::atomic_exchange(value, (__pyx_nonatomic_ptr_type)new_value)
    #if defined(__PYX_DEBUG_ATOMICS) && defined(_MSC_VER)
        #pragma message ("Using standard C++ atomics")
    #elif defined(__PYX_DEBUG_ATOMICS)
        #warning "Using standard C++ atomics"
    #endif
#elif CYTHON_ATOMICS && (__GNUC__ >= 5 || (__GNUC__ == 4 &&\
                    (__GNUC_MINOR__ > 1 ||\
                    (__GNUC_MINOR__ == 1 && __GNUC_PATCHLEVEL__ >= 2))))
    #define __pyx_atomic_ptr_type void*
    #define __pyx_atomic_incr_relaxed(value) __sync_fetch_and_add(value, 1)
    #define __pyx_atomic_incr_acq_rel(value) __sync_fetch_and_add(value, 1)
    #define __pyx_atomic_decr_acq_rel(value) __sync_fetch_and_sub(value, 1)
    #define __pyx_atomic_sub(value, arg) __sync_fetch_and_sub(value, arg)
    static CYTHON_INLINE int __pyx_atomic_int_cmp_exchange(__pyx_atomic_int_type* value, __pyx_nonatomic_int_type* expected, __pyx_nonatomic_int_type desired) {
        __pyx_nonatomic_int_type old = __sync_val_compare_and_swap(value, *expected, desired);
        int result = old == *expected;
        *expected = old;
        return result;
    }
    #define __pyx_atomic_load(value) __sync_fetch_and_add(value, 0)
    #define __pyx_atomic_store(value, new_value) __sync_lock_test_and_set(value, new_value)
    #define __pyx_atomic_pointer_load_relaxed(value) __sync_fetch_and_add(value, 0)
    #define __pyx_atomic_pointer_load_acquire(value) __sync_fetch_and_add(value, 0)
    #define __pyx_atomic_pointer_exchange(value, new_value) __sync_lock_test_and_set(value, (__pyx_atomic_ptr_type)new_value)
    #ifdef __PYX_DEBUG_ATOMICS
        #warning "Using GNU atomics"
    #endif
#elif CYTHON_ATOMICS && defined(_MSC_VER)
    #include <intrin.h>
    #undef __pyx_atomic_int_type
    #define __pyx_atomic_int_type long
    #define __pyx_atomic_ptr_type void*
    #undef __pyx_nonatomic_int_type
    #define __pyx_nonatomic_int_type long
    #pragma intrinsic (_InterlockedExchangeAdd, _InterlockedExchange, _InterlockedCompareExchange, _InterlockedCompareExchangePointer, _InterlockedExchangePointer)
    #define __pyx_atomic_incr_relaxed(value) _InterlockedExchangeAdd(value, 1)
    #define __pyx_atomic_incr_acq_rel(value) _InterlockedExchangeAdd(value, 1)
    #define __pyx_atomic_decr_acq_rel(value) _InterlockedExchangeAdd(value, -1)
    #define __pyx_atomic_sub(value, arg) _InterlockedExchangeAdd(value, -arg)
    static CYTHON_INLINE int __pyx_atomic_int_cmp_exchange(__pyx_atomic_int_type* value, __pyx_nonatomic_int_type* expected, __pyx_nonatomic_int_type desired) {
        __pyx_nonatomic_int_type old = _InterlockedCompareExchange(value, desired, *expected);
        int result = old == *expected;
        *expected = old;
        return result;
    }
    #define __pyx_atomic_load(value) _InterlockedExchangeAdd(value, 0)
    #define __pyx_atomic_store(value, new_value) _InterlockedExchange(value, new_value)
    #define __pyx_atomic_pointer_load_relaxed(value) *(void * volatile *)value
    #define __pyx_atomic_pointer_load_acquire(value) _InterlockedCompareExchangePointer(value, 0, 0)
    #define __pyx_atomic_pointer_exchange(value, new_value) _InterlockedExchangePointer(value, (__pyx_atomic_ptr_type)new_value)
    #ifdef __PYX_DEBUG_ATOMICS
        #pragma message ("Using MSVC atomics")
    #endif
#else
    #undef CYTHON_ATOMICS
    #define CYTHON_ATOMICS 0
    #ifdef __PYX_DEBUG_ATOMICS
        #warning "Not using atomics"
    #endif
#endif
#if CYTHON_ATOMICS
    #define __pyx_add_acquisition_count(memview)\
             __pyx_atomic_incr_relaxed(__pyx_get_slice_count_pointer(memview))
    #define __pyx_sub_acquisition_count(memview)\
            __pyx_atomic_decr_acq_rel(__pyx_get_slice_count_pointer(memview))
#else
    #define __pyx_add_acquisition_count(memview)\
            __pyx_add_acquisition_count_locked(__pyx_get_slice_count_pointer(memview), memview->lock)
    #define __pyx_sub_acquisition_count(memview)\
            __pyx_sub_acquisition_count_locked(__pyx_get_slice_count_pointer(memview), memview->lock)
#endif

/* IncludeStructmemberH.proto */
#include <structmember.h>

/* CriticalSections.proto */
#if !CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
#define __Pyx_PyCriticalSection void*
#define __Pyx_PyCriticalSection2 void*
#define __Pyx_PyCriticalSection_Begin1(cs, arg) (void)cs
#define __Pyx_PyCriticalSection_Begin2(cs, arg1, arg2) (void)cs
#define __Pyx_PyCriticalSection_End1(cs)
#define __Pyx_PyCriticalSection_End2(cs)
#else
#define __Pyx_PyCriticalSection PyCriticalSection
#define __Pyx_PyCriticalSection2 PyCriticalSection2
#define __Pyx_PyCriticalSection_Begin1 PyCriticalSection_Begin
#define __Pyx_PyCriticalSection_Begin2 PyCriticalSection2_Begin
#define __Pyx_PyCriticalSection_End1 PyCriticalSection_End
#define __Pyx_PyCriticalSection_End2 PyCriticalSection2_End
#endif
#if PY_VERSION_HEX < 0x030d0000 || CYTHON_COMPILING_IN_LIMITED_API
#define __Pyx_BEGIN_CRITICAL_SECTION(o) {
#define __Pyx_END_CRITICAL_SECTION() }
#else
#define __Pyx_BEGIN_CRITICAL_SECTION Py_BEGIN_CRITICAL_SECTION
#define __Pyx_END_CRITICAL_SECTION Py_END_CRITICAL_SECTION
#endif

/* #### Code section: numeric_typedefs ### */

/* "solver_c.pyx":4
 * cimport cython
 * from cpython.mem cimport PyMem_Malloc, PyMem_Free
 * ctypedef unsigned long long ull             # <<<<<<<<<<<<<<
 * ctypedef unsigned int idx_t
 * 
*/
typedef unsigned PY_LONG_LONG __pyx_t_8solver_c_ull;

/* "solver_c.pyx":5
 * from cpython.mem cimport PyMem_Malloc, PyMem_Free
 * ctypedef unsigned long long ull
 * ctypedef unsigned int idx_t             # <<<<<<<<<<<<<<
 * 
 * cdef extern from *:
*/
typedef unsigned int __pyx_t_8solver_c_idx_t;
/* #### Code section: complex_type_declarations ### */
/* #### Code section: type_declarations ### */

/*--- Type declarations ---*/
struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c;

/* "solver_c.pyx":66
 *         X |= v
 * 
 * def solve_c(object problem):             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
*/
struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c {
  PyObject_HEAD
  __pyx_t_8solver_c_ull *__pyx_v_neighbors;
};

/* #### Code section: utility_code_proto ### */

/* --- Runtime support code (head) --- */
/* Refnanny.proto */
#ifndef CYTHON_REFNANNY
  #define CYTHON_REFNANNY 0
#endif
#if CYTHON_REFNANNY
  typedef struct {
    void (*INCREF)(void*, PyObject*, Py_ssize_t);
    void (*DECREF)(void*, PyObject*, Py_ssize_t);
    void (*GOTREF)(void*, PyObject*, Py_ssize_t);
    void (*GIVEREF)(void*, PyObject*, Py_ssize_t);
    void* (*SetupContext)(const char*, Py_ssize_t, const char*);
    void (*FinishContext)(void**);
  } __Pyx_RefNannyAPIStruct;
  static __Pyx_RefNannyAPIStruct *__Pyx_RefNanny = NULL;
  static __Pyx_RefNannyAPIStruct *__Pyx_RefNannyImportAPI(const char *modname);
  #define __Pyx_RefNannyDeclarations void *__pyx_refnanny = NULL;
  #define __Pyx_RefNannySetupContext(name, acquire_gil)\
          if (acquire_gil) {\
              PyGILState_STATE __pyx_gilstate_save = PyGILState_Ensure();\
              __pyx_refnanny = __Pyx_RefNanny->SetupContext((name), (__LINE__), (__FILE__));\
              PyGILState_Release(__pyx_gilstate_save);\
          } else {\
              __pyx_refnanny = __Pyx_RefNanny->SetupContext((name), (__LINE__), (__FILE__));\
          }
  #define __Pyx_RefNannyFinishContextNogil() {\
              PyGILState_STATE __pyx_gilstate_save = PyGILState_Ensure();\
              __Pyx_RefNannyFinishContext();\
              PyGILState_Release(__pyx_gilstate_save);\
          }
  #define __Pyx_RefNannyFinishContextNogil() {\
              PyGILState_STATE __pyx_gilstate_save = PyGILState_Ensure();\
              __Pyx_RefNannyFinishContext();\
              PyGILState_Release(__pyx_gilstate_save);\
          }
  #define __Pyx_RefNannyFinishContext()\
          __Pyx_RefNanny->FinishContext(&__pyx_refnanny)
  #define __Pyx_INCREF(r)  __Pyx_RefNanny->INCREF(__pyx_refnanny, (PyObject *)(r), (__LINE__))
  #define __Pyx_DECREF(r)  __Pyx_RefNanny->DECREF(__pyx_refnanny, (PyObject *)(r), (__LINE__))
  #define __Pyx_GOTREF(r)  __Pyx_RefNanny->GOTREF(__pyx_refnanny, (PyObject *)(r), (__LINE__))
  #define __Pyx_GIVEREF(r) __Pyx_RefNanny->GIVEREF(__pyx_refnanny, (PyObject *)(r), (__LINE__))
  #define __Pyx_XINCREF(r)  do { if((r) == NULL); else {__Pyx_INCREF(r); }} while(0)
  #define __Pyx_XDECREF(r)  do { if((r) == NULL); else {__Pyx_DECREF(r); }} while(0)
  #define __Pyx_XGOTREF(r)  do { if((r) == NULL); else {__Pyx_GOTREF(r); }} while(0)
  #define __Pyx_XGIVEREF(r) do { if((r) == NULL); else {__Pyx_GIVEREF(r);}} while(0)
#else
  #define __Pyx_RefNannyDeclarations
  #define __Pyx_RefNannySetupContext(name, acquire_gil)
  #define __Pyx_RefNannyFinishContextNogil()
  #define __Pyx_RefNannyFinishContext()
  #define __Pyx_INCREF(r) Py_INCREF(r)
  #define __Pyx_DECREF(r) Py_DECREF(r)
  #define __Pyx_GOTREF(r)
  #define __Pyx_GIVEREF(r)
  #define __Pyx_XINCREF(r) Py_XINCREF(r)
  #define __Pyx_XDECREF(r) Py_XDECREF(r)
  #define __Pyx_XGOTREF(r)
  #define __Pyx_XGIVEREF(r)
#endif
#define __Pyx_Py_XDECREF_SET(r, v) do {\
        PyObject *tmp = (PyObject *) r;\
        r = v; Py_XDECREF(tmp);\
    } while (0)
#define __Pyx_XDECREF_SET(r, v) do {\
        PyObject *tmp = (PyObject *) r;\
        r = v; __Pyx_XDECREF(tmp);\
    } while (0)
#define __Pyx_DECREF_SET(r, v) do {\
        PyObject *tmp = (PyObject *) r;\
        r = v; __Pyx_DECREF(tmp);\
    } while (0)
#define __Pyx_CLEAR(r)    do { PyObject* tmp = ((PyObject*)(r)); r = NULL; __Pyx_DECREF(tmp);} while(0)
#define __Pyx_XCLEAR(r)   do { if((r) != NULL) {PyObject* tmp = ((PyObject*)(r)); r = NULL; __Pyx_DECREF(tmp);}} while(0)

/* PyErrExceptionMatches.proto */
#if CYTHON_FAST_THREAD_STATE
#define __Pyx_PyErr_ExceptionMatches(err) __Pyx_PyErr_ExceptionMatchesInState(__pyx_tstate, err)
static CYTHON_INLINE int __Pyx_PyErr_ExceptionMatchesInState(PyThreadState* tstate, PyObject* err);
#else
#define __Pyx_PyErr_ExceptionMatches(err)  PyErr_ExceptionMatches(err)
#endif

/* PyThreadStateGet.proto */
#if CYTHON_FAST_THREAD_STATE
#define __Pyx_PyThreadState_declare  PyThreadState *__pyx_tstate;
#define __Pyx_PyThreadState_assign  __pyx_tstate = __Pyx_PyThreadState_Current;
#if PY_VERSION_HEX >= 0x030C00A6
#define __Pyx_PyErr_Occurred()  (__pyx_tstate->current_exception != NULL)
#define __Pyx_PyErr_CurrentExceptionType()  (__pyx_tstate->current_exception ? (PyObject*) Py_TYPE(__pyx_tstate->current_exception) : (PyObject*) NULL)
#else
#define __Pyx_PyErr_Occurred()  (__pyx_tstate->curexc_type != NULL)
#define __Pyx_PyErr_CurrentExceptionType()  (__pyx_tstate->curexc_type)
#endif
#else
#define __Pyx_PyThreadState_declare
#define __Pyx_PyThreadState_assign
#define __Pyx_PyErr_Occurred()  (PyErr_Occurred() != NULL)
#define __Pyx_PyErr_CurrentExceptionType()  PyErr_Occurred()
#endif

/* PyErrFetchRestore.proto */
#if CYTHON_FAST_THREAD_STATE
#define __Pyx_PyErr_Clear() __Pyx_ErrRestore(NULL, NULL, NULL)
#define __Pyx_ErrRestoreWithState(type, value, tb)  __Pyx_ErrRestoreInState(PyThreadState_GET(), type, value, tb)
#define __Pyx_ErrFetchWithState(type, value, tb)    __Pyx_ErrFetchInState(PyThreadState_GET(), type, value, tb)
#define __Pyx_ErrRestore(type, value, tb)  __Pyx_ErrRestoreInState(__pyx_tstate, type, value, tb)
#define __Pyx_ErrFetch(type, value, tb)    __Pyx_ErrFetchInState(__pyx_tstate, type, value, tb)
static CYTHON_INLINE void __Pyx_ErrRestoreInState(PyThreadState *tstate, PyObject *type, PyObject *value, PyObject *tb);
static CYTHON_INLINE void __Pyx_ErrFetchInState(PyThreadState *tstate, PyObject **type, PyObject **value, PyObject **tb);
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX < 0x030C00A6
#define __Pyx_PyErr_SetNone(exc) (Py_INCREF(exc), __Pyx_ErrRestore((exc), NULL, NULL))
#else
#define __Pyx_PyErr_SetNone(exc) PyErr_SetNone(exc)
#endif
#else
#define __Pyx_PyErr_Clear() PyErr_Clear()
#define __Pyx_PyErr_SetNone(exc) PyErr_SetNone(exc)
#define __Pyx_ErrRestoreWithState(type, value, tb)  PyErr_Restore(type, value, tb)
#define __Pyx_ErrFetchWithState(type, value, tb)  PyErr_Fetch(type, value, tb)
#define __Pyx_ErrRestoreInState(tstate, type, value, tb)  PyErr_Restore(type, value, tb)
#define __Pyx_ErrFetchInState(tstate, type, value, tb)  PyErr_Fetch(type, value, tb)
#define __Pyx_ErrRestore(type, value, tb)  PyErr_Restore(type, value, tb)
#define __Pyx_ErrFetch(type, value, tb)  PyErr_Fetch(type, value, tb)
#endif

/* PyObjectGetAttrStr.proto */
#if CYTHON_USE_TYPE_SLOTS
static CYTHON_INLINE PyObject* __Pyx_PyObject_GetAttrStr(PyObject* obj, PyObject* attr_name);
#else
#define __Pyx_PyObject_GetAttrStr(o,n) PyObject_GetAttr(o,n)
#endif

/* PyObjectGetAttrStrNoError.proto */
static CYTHON_INLINE PyObject* __Pyx_PyObject_GetAttrStrNoError(PyObject* obj, PyObject* attr_name);

/* GetBuiltinName.proto */
static PyObject *__Pyx_GetBuiltinName(PyObject *name);

/* ErrOccurredWithGIL.proto */
static CYTHON_INLINE int __Pyx_ErrOccurredWithGIL(void);

/* TupleAndListFromArray.proto */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject* __Pyx_PyList_FromArray(PyObject *const *src, Py_ssize_t n);
#endif
#if CYTHON_COMPILING_IN_CPYTHON || CYTHON_METH_FASTCALL
static CYTHON_INLINE PyObject* __Pyx_PyTuple_FromArray(PyObject *const *src, Py_ssize_t n);
#endif

/* IncludeStringH.proto */
#include <string.h>

/* BytesEquals.proto */
static CYTHON_INLINE int __Pyx_PyBytes_Equals(PyObject* s1, PyObject* s2, int equals);

/* UnicodeEquals.proto */
static CYTHON_INLINE int __Pyx_PyUnicode_Equals(PyObject* s1, PyObject* s2, int equals);

/* fastcall.proto */
#if CYTHON_AVOID_BORROWED_REFS
    #define __Pyx_ArgRef_VARARGS(args, i) __Pyx_PySequence_ITEM(args, i)
#elif CYTHON_ASSUME_SAFE_MACROS
    #define __Pyx_ArgRef_VARARGS(args, i) __Pyx_NewRef(__Pyx_PyTuple_GET_ITEM(args, i))
#else
    #define __Pyx_ArgRef_VARARGS(args, i) __Pyx_XNewRef(PyTuple_GetItem(args, i))
#endif
#define __Pyx_NumKwargs_VARARGS(kwds) PyDict_Size(kwds)
#define __Pyx_KwValues_VARARGS(args, nargs) NULL
#define __Pyx_GetKwValue_VARARGS(kw, kwvalues, s) __Pyx_PyDict_GetItemStrWithError(kw, s)
#define __Pyx_KwargsAsDict_VARARGS(kw, kwvalues) PyDict_Copy(kw)
#if CYTHON_METH_FASTCALL
    #define __Pyx_ArgRef_FASTCALL(args, i) __Pyx_NewRef(args[i])
    #define __Pyx_NumKwargs_FASTCALL(kwds) __Pyx_PyTuple_GET_SIZE(kwds)
    #define __Pyx_KwValues_FASTCALL(args, nargs) ((args) + (nargs))
    static CYTHON_INLINE PyObject * __Pyx_GetKwValue_FASTCALL(PyObject *kwnames, PyObject *const *kwvalues, PyObject *s);
  #if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x030d0000 || CYTHON_COMPILING_IN_LIMITED_API
    CYTHON_UNUSED static PyObject *__Pyx_KwargsAsDict_FASTCALL(PyObject *kwnames, PyObject *const *kwvalues);
  #else
    #define __Pyx_KwargsAsDict_FASTCALL(kw, kwvalues) _PyStack_AsDict(kwvalues, kw)
  #endif
#else
    #define __Pyx_ArgRef_FASTCALL __Pyx_ArgRef_VARARGS
    #define __Pyx_NumKwargs_FASTCALL __Pyx_NumKwargs_VARARGS
    #define __Pyx_KwValues_FASTCALL __Pyx_KwValues_VARARGS
    #define __Pyx_GetKwValue_FASTCALL __Pyx_GetKwValue_VARARGS
    #define __Pyx_KwargsAsDict_FASTCALL __Pyx_KwargsAsDict_VARARGS
#endif
#define __Pyx_ArgsSlice_VARARGS(args, start, stop) PyTuple_GetSlice(args, start, stop)
#if CYTHON_METH_FASTCALL || (CYTHON_COMPILING_IN_CPYTHON && CYTHON_ASSUME_SAFE_MACROS && !CYTHON_AVOID_BORROWED_REFS)
#define __Pyx_ArgsSlice_FASTCALL(args, start, stop) __Pyx_PyTuple_FromArray(args + start, stop - start)
#else
#define __Pyx_ArgsSlice_FASTCALL(args, start, stop) PyTuple_GetSlice(args, start, stop)
#endif

/* RaiseDoubleKeywords.proto */
static void __Pyx_RaiseDoubleKeywordsError(const char* func_name, PyObject* kw_name);

/* ParseKeywords.proto */
static CYTHON_INLINE int __Pyx_ParseKeywords(
    PyObject *kwds, PyObject *const *kwvalues, PyObject ** const argnames[],
    PyObject *kwds2, PyObject *values[],
    Py_ssize_t num_pos_args, Py_ssize_t num_kwargs,
    const char* function_name,
    int ignore_unknown_kwargs
);

/* CallCFunction.proto */
#define __Pyx_CallCFunction(cfunc, self, args)\
    ((PyCFunction)(void(*)(void))(cfunc)->func)(self, args)
#define __Pyx_CallCFunctionWithKeywords(cfunc, self, args, kwargs)\
    ((PyCFunctionWithKeywords)(void(*)(void))(cfunc)->func)(self, args, kwargs)
#define __Pyx_CallCFunctionFast(cfunc, self, args, nargs)\
    ((__Pyx_PyCFunctionFast)(void(*)(void))(PyCFunction)(cfunc)->func)(self, args, nargs)
#define __Pyx_CallCFunctionFastWithKeywords(cfunc, self, args, nargs, kwnames)\
    ((__Pyx_PyCFunctionFastWithKeywords)(void(*)(void))(PyCFunction)(cfunc)->func)(self, args, nargs, kwnames)

/* PyFunctionFastCall.proto */
#if CYTHON_FAST_PYCALL
#if !CYTHON_VECTORCALL
#define __Pyx_PyFunction_FastCall(func, args, nargs)\
    __Pyx_PyFunction_FastCallDict((func), (args), (nargs), NULL)
static PyObject *__Pyx_PyFunction_FastCallDict(PyObject *func, PyObject *const *args, Py_ssize_t nargs, PyObject *kwargs);
#endif
#define __Pyx_BUILD_ASSERT_EXPR(cond)\
    (sizeof(char [1 - 2*!(cond)]) - 1)
#ifndef Py_MEMBER_SIZE
#define Py_MEMBER_SIZE(type, member) sizeof(((type *)0)->member)
#endif
#if !CYTHON_VECTORCALL
#if PY_VERSION_HEX >= 0x03080000
  #include "frameobject.h"
  #define __Pxy_PyFrame_Initialize_Offsets()
  #define __Pyx_PyFrame_GetLocalsplus(frame)  ((frame)->f_localsplus)
#else
  static size_t __pyx_pyframe_localsplus_offset = 0;
  #include "frameobject.h"
  #define __Pxy_PyFrame_Initialize_Offsets()\
    ((void)__Pyx_BUILD_ASSERT_EXPR(sizeof(PyFrameObject) == offsetof(PyFrameObject, f_localsplus) + Py_MEMBER_SIZE(PyFrameObject, f_localsplus)),\
     (void)(__pyx_pyframe_localsplus_offset = ((size_t)PyFrame_Type.tp_basicsize) - Py_MEMBER_SIZE(PyFrameObject, f_localsplus)))
  #define __Pyx_PyFrame_GetLocalsplus(frame)\
    (assert(__pyx_pyframe_localsplus_offset), (PyObject **)(((char *)(frame)) + __pyx_pyframe_localsplus_offset))
#endif
#endif
#endif

/* PyObjectCall.proto */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject* __Pyx_PyObject_Call(PyObject *func, PyObject *arg, PyObject *kw);
#else
#define __Pyx_PyObject_Call(func, arg, kw) PyObject_Call(func, arg, kw)
#endif

/* PyObjectCallMethO.proto */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallMethO(PyObject *func, PyObject *arg);
#endif

/* PyObjectFastCall.proto */
#define __Pyx_PyObject_FastCall(func, args, nargs)  __Pyx_PyObject_FastCallDict(func, args, (size_t)(nargs), NULL)
static CYTHON_INLINE PyObject* __Pyx_PyObject_FastCallDict(PyObject *func, PyObject * const*args, size_t nargs, PyObject *kwargs);

/* UnpackUnboundCMethod.proto */
typedef struct {
    PyObject *type;
    PyObject **method_name;
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING && CYTHON_ATOMICS
    __pyx_atomic_int_type initialized;
#endif
    PyCFunction func;
    PyObject *method;
    int flag;
} __Pyx_CachedCFunction;
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
static CYTHON_INLINE int __Pyx_CachedCFunction_GetAndSetInitializing(__Pyx_CachedCFunction *cfunc) {
#if !CYTHON_ATOMICS
    return 1;
#else
    __pyx_nonatomic_int_type expected = 0;
    if (__pyx_atomic_int_cmp_exchange(&cfunc->initialized, &expected, 1)) {
        return 0;
    }
    return expected;
#endif
}
static CYTHON_INLINE void __Pyx_CachedCFunction_SetFinishedInitializing(__Pyx_CachedCFunction *cfunc) {
#if CYTHON_ATOMICS
    __pyx_atomic_store(&cfunc->initialized, 2);
#endif
}
#else
#define __Pyx_CachedCFunction_GetAndSetInitializing(cfunc) 2
#define __Pyx_CachedCFunction_SetFinishedInitializing(cfunc)
#endif

/* CallUnboundCMethod2.proto */
CYTHON_UNUSED
static PyObject* __Pyx__CallUnboundCMethod2(__Pyx_CachedCFunction* cfunc, PyObject* self, PyObject* arg1, PyObject* arg2);
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject *__Pyx_CallUnboundCMethod2(__Pyx_CachedCFunction *cfunc, PyObject *self, PyObject *arg1, PyObject *arg2);
#else
#define __Pyx_CallUnboundCMethod2(cfunc, self, arg1, arg2)  __Pyx__CallUnboundCMethod2(cfunc, self, arg1, arg2)
#endif

/* RaiseArgTupleInvalid.proto */
static void __Pyx_RaiseArgtupleInvalid(const char* func_name, int exact,
    Py_ssize_t num_min, Py_ssize_t num_max, Py_ssize_t num_found);

/* PyObjectFastCallMethod.proto */
#if CYTHON_VECTORCALL && PY_VERSION_HEX >= 0x03090000
#define __Pyx_PyObject_FastCallMethod(name, args, nargsf) PyObject_VectorcallMethod(name, args, nargsf, NULL)
#else
static PyObject *__Pyx_PyObject_FastCallMethod(PyObject *name, PyObject *const *args, size_t nargsf);
#endif

/* GetItemInt.proto */
#define __Pyx_GetItemInt(o, i, type, is_signed, to_py_func, is_list, wraparound, boundscheck, has_gil)\
    (__Pyx_fits_Py_ssize_t(i, type, is_signed) ?\
    __Pyx_GetItemInt_Fast(o, (Py_ssize_t)i, is_list, wraparound, boundscheck) :\
    (is_list ? (PyErr_SetString(PyExc_IndexError, "list index out of range"), (PyObject*)NULL) :\
               __Pyx_GetItemInt_Generic(o, to_py_func(i))))
#define __Pyx_GetItemInt_List(o, i, type, is_signed, to_py_func, is_list, wraparound, boundscheck, has_gil)\
    (__Pyx_fits_Py_ssize_t(i, type, is_signed) ?\
    __Pyx_GetItemInt_List_Fast(o, (Py_ssize_t)i, wraparound, boundscheck) :\
    (PyErr_SetString(PyExc_IndexError, "list index out of range"), (PyObject*)NULL))
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_List_Fast(PyObject *o, Py_ssize_t i,
                                                              int wraparound, int boundscheck);
#define __Pyx_GetItemInt_Tuple(o, i, type, is_signed, to_py_func, is_list, wraparound, boundscheck, has_gil)\
    (__Pyx_fits_Py_ssize_t(i, type, is_signed) ?\
    __Pyx_GetItemInt_Tuple_Fast(o, (Py_ssize_t)i, wraparound, boundscheck) :\
    (PyErr_SetString(PyExc_IndexError, "tuple index out of range"), (PyObject*)NULL))
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_Tuple_Fast(PyObject *o, Py_ssize_t i,
                                                              int wraparound, int boundscheck);
static PyObject *__Pyx_GetItemInt_Generic(PyObject *o, PyObject* j);
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_Fast(PyObject *o, Py_ssize_t i,
                                                     int is_list, int wraparound, int boundscheck);

/* LimitedApiGetTypeDict.proto */
#if CYTHON_COMPILING_IN_LIMITED_API
static PyObject *__Pyx_GetTypeDict(PyTypeObject *tp);
#endif

/* SetItemOnTypeDict.proto */
static int __Pyx__SetItemOnTypeDict(PyTypeObject *tp, PyObject *k, PyObject *v);
#define __Pyx_SetItemOnTypeDict(tp, k, v) __Pyx__SetItemOnTypeDict((PyTypeObject*)tp, k, v)

/* FixUpExtensionType.proto */
static CYTHON_INLINE int __Pyx_fix_up_extension_type_from_spec(PyType_Spec *spec, PyTypeObject *type);

/* FetchSharedCythonModule.proto */
static PyObject *__Pyx_FetchSharedCythonABIModule(void);

/* dict_setdefault.proto */
static CYTHON_INLINE PyObject *__Pyx_PyDict_SetDefault(PyObject *d, PyObject *key, PyObject *default_value, int is_safe_type);

/* FetchCommonType.proto */
static PyTypeObject* __Pyx_FetchCommonTypeFromSpec(PyTypeObject *metaclass, PyObject *module, PyType_Spec *spec, PyObject *bases);

/* CommonTypesMetaclass.proto */
static int __pyx_CommonTypesMetaclass_init(PyObject *module);
#define __Pyx_CommonTypesMetaclass_USED

/* CallTypeTraverse.proto */
#if !CYTHON_USE_TYPE_SPECS || (!CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX < 0x03090000)
#define __Pyx_call_type_traverse(o, always_call, visit, arg) 0
#else
static int __Pyx_call_type_traverse(PyObject *o, int always_call, visitproc visit, void *arg);
#endif

/* PyMethodNew.proto */
static PyObject *__Pyx_PyMethod_New(PyObject *func, PyObject *self, PyObject *typ);

/* PyVectorcallFastCallDict.proto */
#if CYTHON_METH_FASTCALL && (CYTHON_VECTORCALL || CYTHON_BACKPORT_VECTORCALL)
static CYTHON_INLINE PyObject *__Pyx_PyVectorcall_FastCallDict(PyObject *func, __pyx_vectorcallfunc vc, PyObject *const *args, size_t nargs, PyObject *kw);
#endif

/* CythonFunctionShared.proto */
#define __Pyx_CyFunction_USED
#define __Pyx_CYFUNCTION_STATICMETHOD  0x01
#define __Pyx_CYFUNCTION_CLASSMETHOD   0x02
#define __Pyx_CYFUNCTION_CCLASS        0x04
#define __Pyx_CYFUNCTION_COROUTINE     0x08
#define __Pyx_CyFunction_GetClosure(f)\
    (((__pyx_CyFunctionObject *) (f))->func_closure)
#if PY_VERSION_HEX < 0x030900B1 || CYTHON_COMPILING_IN_LIMITED_API
  #define __Pyx_CyFunction_GetClassObj(f)\
      (((__pyx_CyFunctionObject *) (f))->func_classobj)
#else
  #define __Pyx_CyFunction_GetClassObj(f)\
      ((PyObject*) ((PyCMethodObject *) (f))->mm_class)
#endif
#define __Pyx_CyFunction_SetClassObj(f, classobj)\
    __Pyx__CyFunction_SetClassObj((__pyx_CyFunctionObject *) (f), (classobj))
#define __Pyx_CyFunction_Defaults(type, f)\
    ((type *)(((__pyx_CyFunctionObject *) (f))->defaults))
#define __Pyx_CyFunction_SetDefaultsGetter(f, g)\
    ((__pyx_CyFunctionObject *) (f))->defaults_getter = (g)
typedef struct {
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject_HEAD
    PyObject *func;
#elif PY_VERSION_HEX < 0x030900B1
    PyCFunctionObject func;
#else
    PyCMethodObject func;
#endif
#if CYTHON_BACKPORT_VECTORCALL ||\
        (CYTHON_COMPILING_IN_LIMITED_API && CYTHON_METH_FASTCALL)
    __pyx_vectorcallfunc func_vectorcall;
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject *func_weakreflist;
#endif
    PyObject *func_dict;
    PyObject *func_name;
    PyObject *func_qualname;
    PyObject *func_doc;
    PyObject *func_globals;
    PyObject *func_code;
    PyObject *func_closure;
#if PY_VERSION_HEX < 0x030900B1 || CYTHON_COMPILING_IN_LIMITED_API
    PyObject *func_classobj;
#endif
    PyObject *defaults;
    int flags;
    PyObject *defaults_tuple;
    PyObject *defaults_kwdict;
    PyObject *(*defaults_getter)(PyObject *);
    PyObject *func_annotations;
    PyObject *func_is_coroutine;
} __pyx_CyFunctionObject;
#undef __Pyx_CyOrPyCFunction_Check
#define __Pyx_CyFunction_Check(obj)  __Pyx_TypeCheck(obj, __pyx_mstate_global->__pyx_CyFunctionType)
#define __Pyx_CyOrPyCFunction_Check(obj)  __Pyx_TypeCheck2(obj, __pyx_mstate_global->__pyx_CyFunctionType, &PyCFunction_Type)
#define __Pyx_CyFunction_CheckExact(obj)  __Pyx_IS_TYPE(obj, __pyx_mstate_global->__pyx_CyFunctionType)
static CYTHON_INLINE int __Pyx__IsSameCyOrCFunction(PyObject *func, void (*cfunc)(void));
#undef __Pyx_IsSameCFunction
#define __Pyx_IsSameCFunction(func, cfunc)   __Pyx__IsSameCyOrCFunction(func, cfunc)
static PyObject *__Pyx_CyFunction_Init(__pyx_CyFunctionObject* op, PyMethodDef *ml,
                                      int flags, PyObject* qualname,
                                      PyObject *closure,
                                      PyObject *module, PyObject *globals,
                                      PyObject* code);
static CYTHON_INLINE void __Pyx__CyFunction_SetClassObj(__pyx_CyFunctionObject* f, PyObject* classobj);
static CYTHON_INLINE PyObject *__Pyx_CyFunction_InitDefaults(PyObject *func,
                                                         PyTypeObject *defaults_type);
static CYTHON_INLINE void __Pyx_CyFunction_SetDefaultsTuple(PyObject *m,
                                                            PyObject *tuple);
static CYTHON_INLINE void __Pyx_CyFunction_SetDefaultsKwDict(PyObject *m,
                                                             PyObject *dict);
static CYTHON_INLINE void __Pyx_CyFunction_SetAnnotationsDict(PyObject *m,
                                                              PyObject *dict);
static int __pyx_CyFunction_init(PyObject *module);
#if CYTHON_METH_FASTCALL
static PyObject * __Pyx_CyFunction_Vectorcall_NOARGS(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames);
static PyObject * __Pyx_CyFunction_Vectorcall_O(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames);
static PyObject * __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames);
static PyObject * __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS_METHOD(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames);
#if CYTHON_BACKPORT_VECTORCALL || CYTHON_COMPILING_IN_LIMITED_API
#define __Pyx_CyFunction_func_vectorcall(f) (((__pyx_CyFunctionObject*)f)->func_vectorcall)
#else
#define __Pyx_CyFunction_func_vectorcall(f) (((PyCFunctionObject*)f)->vectorcall)
#endif
#endif

/* CythonFunction.proto */
static PyObject *__Pyx_CyFunction_New(PyMethodDef *ml,
                                      int flags, PyObject* qualname,
                                      PyObject *closure,
                                      PyObject *module, PyObject *globals,
                                      PyObject* code);

/* PyObjectVectorCallKwBuilder.proto */
CYTHON_UNUSED static int __Pyx_VectorcallBuilder_AddArg_Check(PyObject *key, PyObject *value, PyObject *builder, PyObject **args, int n);
#if CYTHON_VECTORCALL
#if PY_VERSION_HEX >= 0x03090000
#define __Pyx_Object_Vectorcall_CallFromBuilder PyObject_Vectorcall
#else
#define __Pyx_Object_Vectorcall_CallFromBuilder _PyObject_Vectorcall
#endif
#define __Pyx_MakeVectorcallBuilderKwds(n) PyTuple_New(n)
static int __Pyx_VectorcallBuilder_AddArg(PyObject *key, PyObject *value, PyObject *builder, PyObject **args, int n);
static int __Pyx_VectorcallBuilder_AddArgStr(const char *key, PyObject *value, PyObject *builder, PyObject **args, int n);
#else
#define __Pyx_Object_Vectorcall_CallFromBuilder __Pyx_PyObject_FastCallDict
#define __Pyx_MakeVectorcallBuilderKwds(n) __Pyx_PyDict_NewPresized(n)
#define __Pyx_VectorcallBuilder_AddArg(key, value, builder, args, n) PyDict_SetItem(builder, key, value)
#define __Pyx_VectorcallBuilder_AddArgStr(key, value, builder, args, n) PyDict_SetItemString(builder, key, value)
#endif

/* PyObjectVectorCallMethodKwBuilder.proto */
#if CYTHON_VECTORCALL && PY_VERSION_HEX >= 0x03090000
#define __Pyx_Object_VectorcallMethod_CallFromBuilder PyObject_VectorcallMethod
#else
static PyObject *__Pyx_Object_VectorcallMethod_CallFromBuilder(PyObject *name, PyObject *const *args, size_t nargsf, PyObject *kwnames);
#endif

/* ListAppend.proto */
#if CYTHON_USE_PYLIST_INTERNALS && CYTHON_ASSUME_SAFE_MACROS
static CYTHON_INLINE int __Pyx_PyList_Append(PyObject* list, PyObject* x) {
    PyListObject* L = (PyListObject*) list;
    Py_ssize_t len = Py_SIZE(list);
    if (likely(L->allocated > len) & likely(len > (L->allocated >> 1))) {
        Py_INCREF(x);
        #if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x030d0000
        L->ob_item[len] = x;
        #else
        PyList_SET_ITEM(list, len, x);
        #endif
        __Pyx_SET_SIZE(list, len + 1);
        return 0;
    }
    return PyList_Append(list, x);
}
#else
#define __Pyx_PyList_Append(L,x) PyList_Append(L,x)
#endif

/* PyObjectCallNoArg.proto */
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallNoArg(PyObject *func);

/* PyObjectCallOneArg.proto */
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallOneArg(PyObject *func, PyObject *arg);

/* PyObjectGetMethod.proto */
static int __Pyx_PyObject_GetMethod(PyObject *obj, PyObject *name, PyObject **method);

/* PyObjectCallMethod0.proto */
static PyObject* __Pyx_PyObject_CallMethod0(PyObject* obj, PyObject* method_name);

/* ValidateBasesTuple.proto */
#if CYTHON_COMPILING_IN_CPYTHON || CYTHON_COMPILING_IN_LIMITED_API || CYTHON_USE_TYPE_SPECS
static int __Pyx_validate_bases_tuple(const char *type_name, Py_ssize_t dictoffset, PyObject *bases);
#endif

/* PyType_Ready.proto */
CYTHON_UNUSED static int __Pyx_PyType_Ready(PyTypeObject *t);

/* PyDictVersioning.proto */
#if CYTHON_USE_DICT_VERSIONS && CYTHON_USE_TYPE_SLOTS
#define __PYX_DICT_VERSION_INIT  ((PY_UINT64_T) -1)
#define __PYX_GET_DICT_VERSION(dict)  (((PyDictObject*)(dict))->ma_version_tag)
#define __PYX_UPDATE_DICT_CACHE(dict, value, cache_var, version_var)\
    (version_var) = __PYX_GET_DICT_VERSION(dict);\
    (cache_var) = (value);
#define __PYX_PY_DICT_LOOKUP_IF_MODIFIED(VAR, DICT, LOOKUP) {\
    static PY_UINT64_T __pyx_dict_version = 0;\
    static PyObject *__pyx_dict_cached_value = NULL;\
    if (likely(__PYX_GET_DICT_VERSION(DICT) == __pyx_dict_version)) {\
        (VAR) = __pyx_dict_cached_value;\
    } else {\
        (VAR) = __pyx_dict_cached_value = (LOOKUP);\
        __pyx_dict_version = __PYX_GET_DICT_VERSION(DICT);\
    }\
}
static CYTHON_INLINE PY_UINT64_T __Pyx_get_tp_dict_version(PyObject *obj);
static CYTHON_INLINE PY_UINT64_T __Pyx_get_object_dict_version(PyObject *obj);
static CYTHON_INLINE int __Pyx_object_dict_version_matches(PyObject* obj, PY_UINT64_T tp_dict_version, PY_UINT64_T obj_dict_version);
#else
#define __PYX_GET_DICT_VERSION(dict)  (0)
#define __PYX_UPDATE_DICT_CACHE(dict, value, cache_var, version_var)
#define __PYX_PY_DICT_LOOKUP_IF_MODIFIED(VAR, DICT, LOOKUP)  (VAR) = (LOOKUP);
#endif

/* CLineInTraceback.proto */
#if CYTHON_CLINE_IN_TRACEBACK && CYTHON_CLINE_IN_TRACEBACK_RUNTIME
static int __Pyx_CLineForTraceback(PyThreadState *tstate, int c_line);
#else
#define __Pyx_CLineForTraceback(tstate, c_line)  (((CYTHON_CLINE_IN_TRACEBACK)) ? c_line : 0)
#endif

/* CodeObjectCache.proto */
#if CYTHON_COMPILING_IN_LIMITED_API
typedef PyObject __Pyx_CachedCodeObjectType;
#else
typedef PyCodeObject __Pyx_CachedCodeObjectType;
#endif
typedef struct {
    __Pyx_CachedCodeObjectType* code_object;
    int code_line;
} __Pyx_CodeObjectCacheEntry;
struct __Pyx_CodeObjectCache {
    int count;
    int max_count;
    __Pyx_CodeObjectCacheEntry* entries;
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    __pyx_atomic_int_type accessor_count;
  #endif
};
static int __pyx_bisect_code_objects(__Pyx_CodeObjectCacheEntry* entries, int count, int code_line);
static __Pyx_CachedCodeObjectType *__pyx_find_code_object(int code_line);
static void __pyx_insert_code_object(int code_line, __Pyx_CachedCodeObjectType* code_object);

/* AddTraceback.proto */
static void __Pyx_AddTraceback(const char *funcname, int c_line,
                               int py_line, const char *filename);

/* GCCDiagnostics.proto */
#if !defined(__INTEL_COMPILER) && defined(__GNUC__) && (__GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 6))
#define __Pyx_HAS_GCC_DIAGNOSTIC
#endif

/* CIntFromPy.proto */
static CYTHON_INLINE int __Pyx_PyLong_As_int(PyObject *);

/* CIntToPy.proto */
static CYTHON_INLINE PyObject* __Pyx_PyLong_From_unsigned_PY_LONG_LONG(unsigned PY_LONG_LONG value);

/* FormatTypeName.proto */
#if CYTHON_COMPILING_IN_LIMITED_API
typedef PyObject *__Pyx_TypeName;
#define __Pyx_FMT_TYPENAME "%U"
#define __Pyx_DECREF_TypeName(obj) Py_XDECREF(obj)
#if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
#define __Pyx_PyType_GetFullyQualifiedName PyType_GetFullyQualifiedName
#else
static __Pyx_TypeName __Pyx_PyType_GetFullyQualifiedName(PyTypeObject* tp);
#endif
#else  // !LIMITED_API
typedef const char *__Pyx_TypeName;
#define __Pyx_FMT_TYPENAME "%.200s"
#define __Pyx_PyType_GetFullyQualifiedName(tp) ((tp)->tp_name)
#define __Pyx_DECREF_TypeName(obj)
#endif

/* CIntToPy.proto */
static CYTHON_INLINE PyObject* __Pyx_PyLong_From_long(long value);

/* CIntFromPy.proto */
static CYTHON_INLINE long __Pyx_PyLong_As_long(PyObject *);

/* FastTypeChecks.proto */
#if CYTHON_COMPILING_IN_CPYTHON
#define __Pyx_TypeCheck(obj, type) __Pyx_IsSubtype(Py_TYPE(obj), (PyTypeObject *)type)
#define __Pyx_TypeCheck2(obj, type1, type2) __Pyx_IsAnySubtype2(Py_TYPE(obj), (PyTypeObject *)type1, (PyTypeObject *)type2)
static CYTHON_INLINE int __Pyx_IsSubtype(PyTypeObject *a, PyTypeObject *b);
static CYTHON_INLINE int __Pyx_IsAnySubtype2(PyTypeObject *cls, PyTypeObject *a, PyTypeObject *b);
static CYTHON_INLINE int __Pyx_PyErr_GivenExceptionMatches(PyObject *err, PyObject *type);
static CYTHON_INLINE int __Pyx_PyErr_GivenExceptionMatches2(PyObject *err, PyObject *type1, PyObject *type2);
#else
#define __Pyx_TypeCheck(obj, type) PyObject_TypeCheck(obj, (PyTypeObject *)type)
#define __Pyx_TypeCheck2(obj, type1, type2) (PyObject_TypeCheck(obj, (PyTypeObject *)type1) || PyObject_TypeCheck(obj, (PyTypeObject *)type2))
#define __Pyx_PyErr_GivenExceptionMatches(err, type) PyErr_GivenExceptionMatches(err, type)
static CYTHON_INLINE int __Pyx_PyErr_GivenExceptionMatches2(PyObject *err, PyObject *type1, PyObject *type2) {
    return PyErr_GivenExceptionMatches(err, type1) || PyErr_GivenExceptionMatches(err, type2);
}
#endif
#define __Pyx_PyErr_ExceptionMatches2(err1, err2)  __Pyx_PyErr_GivenExceptionMatches2(__Pyx_PyErr_CurrentExceptionType(), err1, err2)
#define __Pyx_PyException_Check(obj) __Pyx_TypeCheck(obj, PyExc_Exception)
#ifdef PyExceptionInstance_Check
  #define __Pyx_PyBaseException_Check(obj) PyExceptionInstance_Check(obj)
#else
  #define __Pyx_PyBaseException_Check(obj) __Pyx_TypeCheck(obj, PyExc_BaseException)
#endif

/* GetRuntimeVersion.proto */
static unsigned long __Pyx_get_runtime_version(void);

/* CheckBinaryVersion.proto */
static int __Pyx_check_binary_version(unsigned long ct_version, unsigned long rt_version, int allow_newer);

/* MultiPhaseInitModuleState.proto */
#if CYTHON_PEP489_MULTI_PHASE_INIT && CYTHON_USE_MODULE_STATE
static PyObject *__Pyx_State_FindModule(void*);
static int __Pyx_State_AddModule(PyObject* module, void*);
static int __Pyx_State_RemoveModule(void*);
#elif CYTHON_USE_MODULE_STATE
#define __Pyx_State_FindModule PyState_FindModule
#define __Pyx_State_AddModule PyState_AddModule
#define __Pyx_State_RemoveModule PyState_RemoveModule
#endif

/* #### Code section: module_declarations ### */
/* CythonABIVersion.proto */
#if CYTHON_COMPILING_IN_LIMITED_API
    #if CYTHON_METH_FASTCALL
        #define __PYX_FASTCALL_ABI_SUFFIX  "_fastcall"
    #else
        #define __PYX_FASTCALL_ABI_SUFFIX
    #endif
    #define __PYX_LIMITED_ABI_SUFFIX "limited" __PYX_FASTCALL_ABI_SUFFIX __PYX_AM_SEND_ABI_SUFFIX
#else
    #define __PYX_LIMITED_ABI_SUFFIX
#endif
#if __PYX_HAS_PY_AM_SEND == 1
    #define __PYX_AM_SEND_ABI_SUFFIX
#elif __PYX_HAS_PY_AM_SEND == 2
    #define __PYX_AM_SEND_ABI_SUFFIX "amsendbackport"
#else
    #define __PYX_AM_SEND_ABI_SUFFIX "noamsend"
#endif
#ifndef __PYX_MONITORING_ABI_SUFFIX
    #define __PYX_MONITORING_ABI_SUFFIX
#endif
#if CYTHON_USE_TP_FINALIZE
    #define __PYX_TP_FINALIZE_ABI_SUFFIX
#else
    #define __PYX_TP_FINALIZE_ABI_SUFFIX "nofinalize"
#endif
#if CYTHON_USE_FREELISTS || !defined(__Pyx_AsyncGen_USED)
    #define __PYX_FREELISTS_ABI_SUFFIX
#else
    #define __PYX_FREELISTS_ABI_SUFFIX "nofreelists"
#endif
#define CYTHON_ABI  __PYX_ABI_VERSION __PYX_LIMITED_ABI_SUFFIX __PYX_MONITORING_ABI_SUFFIX __PYX_TP_FINALIZE_ABI_SUFFIX __PYX_FREELISTS_ABI_SUFFIX __PYX_AM_SEND_ABI_SUFFIX
#define __PYX_ABI_MODULE_NAME "_cython_" CYTHON_ABI
#define __PYX_TYPE_MODULE_PREFIX __PYX_ABI_MODULE_NAME "."


/* Module declarations from "cython" */

/* Module declarations from "cpython.mem" */

/* Module declarations from "solver_c" */
static CYTHON_INLINE int __pyx_f_8solver_c_bc(__pyx_t_8solver_c_ull); /*proto*/
static CYTHON_INLINE __pyx_t_8solver_c_idx_t __pyx_f_8solver_c_ctz(__pyx_t_8solver_c_ull); /*proto*/
static CYTHON_INLINE int __pyx_f_8solver_c_color_bound(__pyx_t_8solver_c_ull, __pyx_t_8solver_c_ull *); /*proto*/
static void __pyx_f_8solver_c_bronk(__pyx_t_8solver_c_ull, __pyx_t_8solver_c_ull, __pyx_t_8solver_c_ull, int *, __pyx_t_8solver_c_ull *, __pyx_t_8solver_c_ull *, __pyx_t_8solver_c_idx_t); /*proto*/
/* #### Code section: typeinfo ### */
/* #### Code section: before_global_var ### */
#define __Pyx_MODULE_NAME "solver_c"
extern int __pyx_module_is_main_solver_c;
int __pyx_module_is_main_solver_c = 0;

/* Implementation of "solver_c" */
/* #### Code section: global_var ### */
static PyObject *__pyx_builtin_range;
/* #### Code section: string_decls ### */
static const char __pyx_k_[] = "?";
static const char __pyx_k_i[] = "i";
static const char __pyx_k_j[] = "j";
static const char __pyx_k_n[] = "n";
static const char __pyx_k_x[] = "x";
static const char __pyx_k_R0[] = "R0";
static const char __pyx_k_gc[] = "gc";
static const char __pyx_k_key[] = "key";
static const char __pyx_k_pop[] = "pop";
static const char __pyx_k_res[] = "res";
static const char __pyx_k_full[] = "full";
static const char __pyx_k_func[] = "__func__";
static const char __pyx_k_iq_Q[] = "\220;\230i\240q\250\003\250:\260Q";
static const char __pyx_k_main[] = "__main__";
static const char __pyx_k_mask[] = "mask";
static const char __pyx_k_name[] = "__name__";
static const char __pyx_k_sort[] = "sort";
static const char __pyx_k_test[] = "__test__";
static const char __pyx_k_bestR[] = "bestR";
static const char __pyx_k_order[] = "order";
static const char __pyx_k_range[] = "range";
static const char __pyx_k_enable[] = "enable";
static const char __pyx_k_lambda[] = "<lambda>";
static const char __pyx_k_module[] = "__module__";
static const char __pyx_k_bestR_p[] = "bestR_p";
static const char __pyx_k_disable[] = "disable";
static const char __pyx_k_problem[] = "problem";
static const char __pyx_k_solve_c[] = "solve_c";
static const char __pyx_k_qualname[] = "__qualname__";
static const char __pyx_k_set_name[] = "__set_name__";
static const char __pyx_k_solver_c[] = "solver_c";
static const char __pyx_k_best_size[] = "best_size";
static const char __pyx_k_bit_count[] = "bit_count";
static const char __pyx_k_isenabled[] = "isenabled";
static const char __pyx_k_neighbors[] = "neighbors";
static const char __pyx_k_best_size_p[] = "best_size_p";
static const char __pyx_k_is_coroutine[] = "_is_coroutine";
static const char __pyx_k_solver_c_pyx[] = "solver_c.pyx";
static const char __pyx_k_asyncio_coroutines[] = "asyncio.coroutines";
static const char __pyx_k_cline_in_traceback[] = "cline_in_traceback";
static const char __pyx_k_solve_c_locals_lambda[] = "solve_c.<locals>.<lambda>";
static const char __pyx_k_1A_Qb_AQ_E_3c_1_U_1_uBb_Rs_E_aq[] = "\200\001\330\004\030\230\003\2301\230A\330\004\032\230'\240\034\250Q\250b\260\002\260!\360\n\000\005\035\230A\230Q\330\004\030\230\001\230\021\340\004\014\210E\220\022\2203\220c\230\022\2301\330\004\010\210\005\210U\220!\2201\330\010\017\210u\220B\220b\230\005\230R\230s\240!\330\010\014\210E\220\025\220a\220q\330\014\020\220\005\220W\230A\230R\230q\240\001\330\020\030\230\002\230%\230r\240\023\240A\330\010\021\220\021\220%\220q\360\006\000\005\027\220d\230!\2305\240\001\240\021\330\004\t\210\025\210a\210t\2201\330\004\022\220!\330\004\010\210\005\210Q\330\010\014\210C\210r\220\031\230!\2304\230s\240!\330\014\023\2205\230\002\230#\230Q\340\004\020\220\002\220!\2201\330\004\014\210A\340\004\t\210\021\210%\210s\220&\230\005\230S\240\r\250Y\260k\300\027\310\001\360\006\000\005\025\220A\330\004\010\210\005\210U\220!\2201\330\010\014\210F\220#\220S\230\002\230!\330\014\017\210w\220a\220q\340\004\016\210a\210q\330\004\013\2101";
/* #### Code section: decls ### */
static PyObject *__pyx_lambda_funcdef_lambda(PyObject *__pyx_self, PyObject *__pyx_v_x); /* proto */
static PyObject *__pyx_pf_8solver_c_solve_c(CYTHON_UNUSED PyObject *__pyx_self, PyObject *__pyx_v_problem); /* proto */
static PyObject *__pyx_tp_new_8solver_c___pyx_scope_struct__solve_c(PyTypeObject *t, PyObject *a, PyObject *k); /*proto*/
/* #### Code section: late_includes ### */
/* #### Code section: module_state ### */
/* SmallCodeConfig */
#ifndef CYTHON_SMALL_CODE
#if defined(__clang__)
    #define CYTHON_SMALL_CODE
#elif defined(__GNUC__) && (__GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 3))
    #define CYTHON_SMALL_CODE __attribute__((cold))
#else
    #define CYTHON_SMALL_CODE
#endif
#endif

typedef struct {
  PyObject *__pyx_d;
  PyObject *__pyx_b;
  PyObject *__pyx_cython_runtime;
  PyObject *__pyx_empty_tuple;
  PyObject *__pyx_empty_bytes;
  PyObject *__pyx_empty_unicode;
  #ifdef __Pyx_CyFunction_USED
  PyTypeObject *__pyx_CyFunctionType;
  #endif
  #ifdef __Pyx_FusedFunction_USED
  PyTypeObject *__pyx_FusedFunctionType;
  #endif
  #ifdef __Pyx_Generator_USED
  PyTypeObject *__pyx_GeneratorType;
  #endif
  #ifdef __Pyx_IterableCoroutine_USED
  PyTypeObject *__pyx_IterableCoroutineType;
  #endif
  #ifdef __Pyx_Coroutine_USED
  PyTypeObject *__pyx_CoroutineAwaitType;
  #endif
  #ifdef __Pyx_Coroutine_USED
  PyTypeObject *__pyx_CoroutineType;
  #endif
  PyObject *__pyx_type_8solver_c___pyx_scope_struct__solve_c;
  PyTypeObject *__pyx_ptype_8solver_c___pyx_scope_struct__solve_c;
  __Pyx_CachedCFunction __pyx_umethod_PyDict_Type_pop;
  PyObject *__pyx_codeobj_tab[2];
  PyObject *__pyx_string_tab[40];
/* #### Code section: module_state_contents ### */
/* CommonTypesMetaclass.module_state_decls */
PyTypeObject *__pyx_CommonTypesMetaclassType;

/* CachedMethodType.module_state_decls */
#if CYTHON_COMPILING_IN_LIMITED_API
PyObject *__Pyx_CachedMethodType;
#endif


#if CYTHON_USE_FREELISTS
struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *__pyx_freelist_8solver_c___pyx_scope_struct__solve_c[8];
int __pyx_freecount_8solver_c___pyx_scope_struct__solve_c;
#endif
/* CodeObjectCache.module_state_decls */
struct __Pyx_CodeObjectCache __pyx_code_cache;

/* #### Code section: module_state_end ### */
} __pyx_mstatetype;

#if CYTHON_USE_MODULE_STATE
#ifdef __cplusplus
namespace {
extern struct PyModuleDef __pyx_moduledef;
} /* anonymous namespace */
#else
static struct PyModuleDef __pyx_moduledef;
#endif

#define __pyx_mstate_global (__Pyx_PyModule_GetState(__Pyx_State_FindModule(&__pyx_moduledef)))

#define __pyx_m (__Pyx_State_FindModule(&__pyx_moduledef))
#else
static __pyx_mstatetype __pyx_mstate_global_static =
#ifdef __cplusplus
    {};
#else
    {0};
#endif
static __pyx_mstatetype * const __pyx_mstate_global = &__pyx_mstate_global_static;
#endif
/* #### Code section: constant_name_defines ### */
#define __pyx_kp_u_ __pyx_string_tab[0]
#define __pyx_n_u_R0 __pyx_string_tab[1]
#define __pyx_n_u_asyncio_coroutines __pyx_string_tab[2]
#define __pyx_n_u_bestR __pyx_string_tab[3]
#define __pyx_n_u_bestR_p __pyx_string_tab[4]
#define __pyx_n_u_best_size __pyx_string_tab[5]
#define __pyx_n_u_best_size_p __pyx_string_tab[6]
#define __pyx_n_u_bit_count __pyx_string_tab[7]
#define __pyx_n_u_cline_in_traceback __pyx_string_tab[8]
#define __pyx_kp_u_disable __pyx_string_tab[9]
#define __pyx_kp_u_enable __pyx_string_tab[10]
#define __pyx_n_u_full __pyx_string_tab[11]
#define __pyx_n_u_func __pyx_string_tab[12]
#define __pyx_kp_u_gc __pyx_string_tab[13]
#define __pyx_n_u_i __pyx_string_tab[14]
#define __pyx_n_u_is_coroutine __pyx_string_tab[15]
#define __pyx_kp_u_isenabled __pyx_string_tab[16]
#define __pyx_n_u_j __pyx_string_tab[17]
#define __pyx_n_u_key __pyx_string_tab[18]
#define __pyx_n_u_lambda __pyx_string_tab[19]
#define __pyx_n_u_main __pyx_string_tab[20]
#define __pyx_n_u_mask __pyx_string_tab[21]
#define __pyx_n_u_module __pyx_string_tab[22]
#define __pyx_n_u_n __pyx_string_tab[23]
#define __pyx_n_u_name __pyx_string_tab[24]
#define __pyx_n_u_neighbors __pyx_string_tab[25]
#define __pyx_n_u_order __pyx_string_tab[26]
#define __pyx_n_u_pop __pyx_string_tab[27]
#define __pyx_n_u_problem __pyx_string_tab[28]
#define __pyx_n_u_qualname __pyx_string_tab[29]
#define __pyx_n_u_range __pyx_string_tab[30]
#define __pyx_n_u_res __pyx_string_tab[31]
#define __pyx_n_u_set_name __pyx_string_tab[32]
#define __pyx_n_u_solve_c __pyx_string_tab[33]
#define __pyx_n_u_solve_c_locals_lambda __pyx_string_tab[34]
#define __pyx_n_u_solver_c __pyx_string_tab[35]
#define __pyx_kp_u_solver_c_pyx __pyx_string_tab[36]
#define __pyx_n_u_sort __pyx_string_tab[37]
#define __pyx_n_u_test __pyx_string_tab[38]
#define __pyx_n_u_x __pyx_string_tab[39]
/* #### Code section: module_state_clear ### */
#if CYTHON_USE_MODULE_STATE
static CYTHON_SMALL_CODE int __pyx_m_clear(PyObject *m) {
  __pyx_mstatetype *clear_module_state = __Pyx_PyModule_GetState(m);
  if (!clear_module_state) return 0;
  Py_CLEAR(clear_module_state->__pyx_d);
  Py_CLEAR(clear_module_state->__pyx_b);
  Py_CLEAR(clear_module_state->__pyx_cython_runtime);
  Py_CLEAR(clear_module_state->__pyx_empty_tuple);
  Py_CLEAR(clear_module_state->__pyx_empty_bytes);
  Py_CLEAR(clear_module_state->__pyx_empty_unicode);
  #ifdef __Pyx_CyFunction_USED
  Py_CLEAR(clear_module_state->__pyx_CyFunctionType);
  #endif
  #ifdef __Pyx_FusedFunction_USED
  Py_CLEAR(clear_module_state->__pyx_FusedFunctionType);
  #endif
  #if CYTHON_PEP489_MULTI_PHASE_INIT
  __Pyx_State_RemoveModule(NULL);
  #endif
  Py_CLEAR(clear_module_state->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c);
  Py_CLEAR(clear_module_state->__pyx_type_8solver_c___pyx_scope_struct__solve_c);
  for (int i=0; i<2; ++i) { Py_CLEAR(clear_module_state->__pyx_codeobj_tab[i]); }
  for (int i=0; i<40; ++i) { Py_CLEAR(clear_module_state->__pyx_string_tab[i]); }
  return 0;
}
#endif
/* #### Code section: module_state_traverse ### */
#if CYTHON_USE_MODULE_STATE
static CYTHON_SMALL_CODE int __pyx_m_traverse(PyObject *m, visitproc visit, void *arg) {
  __pyx_mstatetype *traverse_module_state = __Pyx_PyModule_GetState(m);
  if (!traverse_module_state) return 0;
  Py_VISIT(traverse_module_state->__pyx_d);
  Py_VISIT(traverse_module_state->__pyx_b);
  Py_VISIT(traverse_module_state->__pyx_cython_runtime);
  __Pyx_VISIT_CONST(traverse_module_state->__pyx_empty_tuple);
  __Pyx_VISIT_CONST(traverse_module_state->__pyx_empty_bytes);
  __Pyx_VISIT_CONST(traverse_module_state->__pyx_empty_unicode);
  #ifdef __Pyx_CyFunction_USED
  Py_VISIT(traverse_module_state->__pyx_CyFunctionType);
  #endif
  #ifdef __Pyx_FusedFunction_USED
  Py_VISIT(traverse_module_state->__pyx_FusedFunctionType);
  #endif
  Py_VISIT(traverse_module_state->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c);
  Py_VISIT(traverse_module_state->__pyx_type_8solver_c___pyx_scope_struct__solve_c);
  for (int i=0; i<2; ++i) { __Pyx_VISIT_CONST(traverse_module_state->__pyx_codeobj_tab[i]); }
  for (int i=0; i<40; ++i) { __Pyx_VISIT_CONST(traverse_module_state->__pyx_string_tab[i]); }
  return 0;
}
#endif
/* #### Code section: module_code ### */

/* "solver_c.pyx":11
 *     unsigned int __builtin_ctzll(unsigned long long) nogil
 * 
 * cdef inline int bc(ull x) nogil:             # <<<<<<<<<<<<<<
 *     return <int>__builtin_popcountll(x)
 * 
*/

static CYTHON_INLINE int __pyx_f_8solver_c_bc(__pyx_t_8solver_c_ull __pyx_v_x) {
  int __pyx_r;

  /* "solver_c.pyx":12
 * 
 * cdef inline int bc(ull x) nogil:
 *     return <int>__builtin_popcountll(x)             # <<<<<<<<<<<<<<
 * 
 * cdef inline idx_t ctz(ull x) nogil:
*/
  __pyx_r = ((int)__builtin_popcountll(__pyx_v_x));
  goto __pyx_L0;

  /* "solver_c.pyx":11
 *     unsigned int __builtin_ctzll(unsigned long long) nogil
 * 
 * cdef inline int bc(ull x) nogil:             # <<<<<<<<<<<<<<
 *     return <int>__builtin_popcountll(x)
 * 
*/

  /* function exit code */
  __pyx_L0:;
  return __pyx_r;
}

/* "solver_c.pyx":14
 *     return <int>__builtin_popcountll(x)
 * 
 * cdef inline idx_t ctz(ull x) nogil:             # <<<<<<<<<<<<<<
 *     return <idx_t>__builtin_ctzll(x)
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:
*/

static CYTHON_INLINE __pyx_t_8solver_c_idx_t __pyx_f_8solver_c_ctz(__pyx_t_8solver_c_ull __pyx_v_x) {
  __pyx_t_8solver_c_idx_t __pyx_r;

  /* "solver_c.pyx":15
 * 
 * cdef inline idx_t ctz(ull x) nogil:
 *     return <idx_t>__builtin_ctzll(x)             # <<<<<<<<<<<<<<
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:
 *     cdef ull uncol = P, cur, v
*/
  __pyx_r = ((__pyx_t_8solver_c_idx_t)__builtin_ctzll(__pyx_v_x));
  goto __pyx_L0;

  /* "solver_c.pyx":14
 *     return <int>__builtin_popcountll(x)
 * 
 * cdef inline idx_t ctz(ull x) nogil:             # <<<<<<<<<<<<<<
 *     return <idx_t>__builtin_ctzll(x)
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:
*/

  /* function exit code */
  __pyx_L0:;
  return __pyx_r;
}

/* "solver_c.pyx":16
 * cdef inline idx_t ctz(ull x) nogil:
 *     return <idx_t>__builtin_ctzll(x)
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:             # <<<<<<<<<<<<<<
 *     cdef ull uncol = P, cur, v
 *     cdef int color = 0
*/

static CYTHON_INLINE int __pyx_f_8solver_c_color_bound(__pyx_t_8solver_c_ull __pyx_v_P, __pyx_t_8solver_c_ull *__pyx_v_neighbors) {
  __pyx_t_8solver_c_ull __pyx_v_uncol;
  __pyx_t_8solver_c_ull __pyx_v_cur;
  __pyx_t_8solver_c_ull __pyx_v_v;
  int __pyx_v_color;
  __pyx_t_8solver_c_idx_t __pyx_v_i;
  int __pyx_r;
  int __pyx_t_1;
  __pyx_t_8solver_c_idx_t __pyx_t_2;
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  PyGILState_STATE __pyx_gilstate_save;

  /* "solver_c.pyx":17
 *     return <idx_t>__builtin_ctzll(x)
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:
 *     cdef ull uncol = P, cur, v             # <<<<<<<<<<<<<<
 *     cdef int color = 0
 *     cdef idx_t i
*/
  __pyx_v_uncol = __pyx_v_P;

  /* "solver_c.pyx":18
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:
 *     cdef ull uncol = P, cur, v
 *     cdef int color = 0             # <<<<<<<<<<<<<<
 *     cdef idx_t i
 *     while uncol:
*/
  __pyx_v_color = 0;

  /* "solver_c.pyx":20
 *     cdef int color = 0
 *     cdef idx_t i
 *     while uncol:             # <<<<<<<<<<<<<<
 *         color += 1
 *         cur = uncol
*/
  while (1) {
    __pyx_t_1 = (__pyx_v_uncol != 0);
    if (!__pyx_t_1) break;

    /* "solver_c.pyx":21
 *     cdef idx_t i
 *     while uncol:
 *         color += 1             # <<<<<<<<<<<<<<
 *         cur = uncol
 *         while cur:
*/
    __pyx_v_color = (__pyx_v_color + 1);

    /* "solver_c.pyx":22
 *     while uncol:
 *         color += 1
 *         cur = uncol             # <<<<<<<<<<<<<<
 *         while cur:
 *             v = cur & -cur
*/
    __pyx_v_cur = __pyx_v_uncol;

    /* "solver_c.pyx":23
 *         color += 1
 *         cur = uncol
 *         while cur:             # <<<<<<<<<<<<<<
 *             v = cur & -cur
 *             cur -= v
*/
    while (1) {
      __pyx_t_1 = (__pyx_v_cur != 0);
      if (!__pyx_t_1) break;

      /* "solver_c.pyx":24
 *         cur = uncol
 *         while cur:
 *             v = cur & -cur             # <<<<<<<<<<<<<<
 *             cur -= v
 *             uncol &= ~v
*/
      __pyx_v_v = (__pyx_v_cur & (-__pyx_v_cur));

      /* "solver_c.pyx":25
 *         while cur:
 *             v = cur & -cur
 *             cur -= v             # <<<<<<<<<<<<<<
 *             uncol &= ~v
 *             i = ctz(v)
*/
      __pyx_v_cur = (__pyx_v_cur - __pyx_v_v);

      /* "solver_c.pyx":26
 *             v = cur & -cur
 *             cur -= v
 *             uncol &= ~v             # <<<<<<<<<<<<<<
 *             i = ctz(v)
 *             cur &= ~neighbors[i]
*/
      __pyx_v_uncol = (__pyx_v_uncol & (~__pyx_v_v));

      /* "solver_c.pyx":27
 *             cur -= v
 *             uncol &= ~v
 *             i = ctz(v)             # <<<<<<<<<<<<<<
 *             cur &= ~neighbors[i]
 *     return color
*/
      __pyx_t_2 = __pyx_f_8solver_c_ctz(__pyx_v_v); if (unlikely(__pyx_t_2 == ((__pyx_t_8solver_c_idx_t)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 27, __pyx_L1_error)
      __pyx_v_i = __pyx_t_2;

      /* "solver_c.pyx":28
 *             uncol &= ~v
 *             i = ctz(v)
 *             cur &= ~neighbors[i]             # <<<<<<<<<<<<<<
 *     return color
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
*/
      __pyx_v_cur = (__pyx_v_cur & (~(__pyx_v_neighbors[__pyx_v_i])));
    }
  }

  /* "solver_c.pyx":29
 *             i = ctz(v)
 *             cur &= ~neighbors[i]
 *     return color             # <<<<<<<<<<<<<<
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
 *     cdef int sizeR = bc(R)
*/
  __pyx_r = __pyx_v_color;
  goto __pyx_L0;

  /* "solver_c.pyx":16
 * cdef inline idx_t ctz(ull x) nogil:
 *     return <idx_t>__builtin_ctzll(x)
 * cdef inline int color_bound(ull P, ull* neighbors) nogil:             # <<<<<<<<<<<<<<
 *     cdef ull uncol = P, cur, v
 *     cdef int color = 0
*/

  /* function exit code */
  __pyx_L1_error:;
  __pyx_gilstate_save = __Pyx_PyGILState_Ensure();
  __Pyx_AddTraceback("solver_c.color_bound", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __pyx_r = -1;
  __Pyx_PyGILState_Release(__pyx_gilstate_save);
  __pyx_L0:;
  return __pyx_r;
}

/* "solver_c.pyx":30
 *             cur &= ~neighbors[i]
 *     return color
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:             # <<<<<<<<<<<<<<
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:
*/

static void __pyx_f_8solver_c_bronk(__pyx_t_8solver_c_ull __pyx_v_R, __pyx_t_8solver_c_ull __pyx_v_P, __pyx_t_8solver_c_ull __pyx_v_X, int *__pyx_v_best_size_p, __pyx_t_8solver_c_ull *__pyx_v_bestR_p, __pyx_t_8solver_c_ull *__pyx_v_neighbors, __pyx_t_8solver_c_idx_t __pyx_v_n) {
  int __pyx_v_sizeR;
  int __pyx_v_bound;
  __pyx_t_8solver_c_ull __pyx_v_PX;
  int __pyx_v_maxd;
  __pyx_t_8solver_c_idx_t __pyx_v_u;
  __pyx_t_8solver_c_ull __pyx_v_tmp;
  __pyx_t_8solver_c_ull __pyx_v_v;
  __pyx_t_8solver_c_idx_t __pyx_v_i;
  int __pyx_v_d;
  __pyx_t_8solver_c_ull __pyx_v_ext;
  int __pyx_t_1;
  int __pyx_t_2;
  int __pyx_t_3;
  __pyx_t_8solver_c_idx_t __pyx_t_4;
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  PyGILState_STATE __pyx_gilstate_save;

  /* "solver_c.pyx":31
 *     return color
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
 *     cdef int sizeR = bc(R)             # <<<<<<<<<<<<<<
 *     if P == 0 and X == 0:
 *         if sizeR > best_size_p[0]:
*/
  __pyx_t_1 = __pyx_f_8solver_c_bc(__pyx_v_R); if (unlikely(__pyx_t_1 == ((int)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 31, __pyx_L1_error)
  __pyx_v_sizeR = __pyx_t_1;

  /* "solver_c.pyx":32
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:             # <<<<<<<<<<<<<<
 *         if sizeR > best_size_p[0]:
 *             best_size_p[0] = sizeR
*/
  __pyx_t_3 = (__pyx_v_P == 0);
  if (__pyx_t_3) {
  } else {
    __pyx_t_2 = __pyx_t_3;
    goto __pyx_L4_bool_binop_done;
  }
  __pyx_t_3 = (__pyx_v_X == 0);
  __pyx_t_2 = __pyx_t_3;
  __pyx_L4_bool_binop_done:;
  if (__pyx_t_2) {

    /* "solver_c.pyx":33
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:
 *         if sizeR > best_size_p[0]:             # <<<<<<<<<<<<<<
 *             best_size_p[0] = sizeR
 *             bestR_p[0] = R
*/
    __pyx_t_2 = (__pyx_v_sizeR > (__pyx_v_best_size_p[0]));
    if (__pyx_t_2) {

      /* "solver_c.pyx":34
 *     if P == 0 and X == 0:
 *         if sizeR > best_size_p[0]:
 *             best_size_p[0] = sizeR             # <<<<<<<<<<<<<<
 *             bestR_p[0] = R
 *         return
*/
      (__pyx_v_best_size_p[0]) = __pyx_v_sizeR;

      /* "solver_c.pyx":35
 *         if sizeR > best_size_p[0]:
 *             best_size_p[0] = sizeR
 *             bestR_p[0] = R             # <<<<<<<<<<<<<<
 *         return
 *     if sizeR + bc(P) <= best_size_p[0]:
*/
      (__pyx_v_bestR_p[0]) = __pyx_v_R;

      /* "solver_c.pyx":33
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:
 *         if sizeR > best_size_p[0]:             # <<<<<<<<<<<<<<
 *             best_size_p[0] = sizeR
 *             bestR_p[0] = R
*/
    }

    /* "solver_c.pyx":36
 *             best_size_p[0] = sizeR
 *             bestR_p[0] = R
 *         return             # <<<<<<<<<<<<<<
 *     if sizeR + bc(P) <= best_size_p[0]:
 *         return
*/
    goto __pyx_L0;

    /* "solver_c.pyx":32
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:             # <<<<<<<<<<<<<<
 *         if sizeR > best_size_p[0]:
 *             best_size_p[0] = sizeR
*/
  }

  /* "solver_c.pyx":37
 *             bestR_p[0] = R
 *         return
 *     if sizeR + bc(P) <= best_size_p[0]:             # <<<<<<<<<<<<<<
 *         return
 *     cdef int bound = color_bound(P, neighbors)
*/
  __pyx_t_1 = __pyx_f_8solver_c_bc(__pyx_v_P); if (unlikely(__pyx_t_1 == ((int)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 37, __pyx_L1_error)
  __pyx_t_2 = ((__pyx_v_sizeR + __pyx_t_1) <= (__pyx_v_best_size_p[0]));
  if (__pyx_t_2) {

    /* "solver_c.pyx":38
 *         return
 *     if sizeR + bc(P) <= best_size_p[0]:
 *         return             # <<<<<<<<<<<<<<
 *     cdef int bound = color_bound(P, neighbors)
 *     if sizeR + bound <= best_size_p[0]:
*/
    goto __pyx_L0;

    /* "solver_c.pyx":37
 *             bestR_p[0] = R
 *         return
 *     if sizeR + bc(P) <= best_size_p[0]:             # <<<<<<<<<<<<<<
 *         return
 *     cdef int bound = color_bound(P, neighbors)
*/
  }

  /* "solver_c.pyx":39
 *     if sizeR + bc(P) <= best_size_p[0]:
 *         return
 *     cdef int bound = color_bound(P, neighbors)             # <<<<<<<<<<<<<<
 *     if sizeR + bound <= best_size_p[0]:
 *         return
*/
  __pyx_t_1 = __pyx_f_8solver_c_color_bound(__pyx_v_P, __pyx_v_neighbors); if (unlikely(__pyx_t_1 == ((int)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 39, __pyx_L1_error)
  __pyx_v_bound = __pyx_t_1;

  /* "solver_c.pyx":40
 *         return
 *     cdef int bound = color_bound(P, neighbors)
 *     if sizeR + bound <= best_size_p[0]:             # <<<<<<<<<<<<<<
 *         return
 *     cdef ull PX = P | X
*/
  __pyx_t_2 = ((__pyx_v_sizeR + __pyx_v_bound) <= (__pyx_v_best_size_p[0]));
  if (__pyx_t_2) {

    /* "solver_c.pyx":41
 *     cdef int bound = color_bound(P, neighbors)
 *     if sizeR + bound <= best_size_p[0]:
 *         return             # <<<<<<<<<<<<<<
 *     cdef ull PX = P | X
 *     cdef int maxd = -1
*/
    goto __pyx_L0;

    /* "solver_c.pyx":40
 *         return
 *     cdef int bound = color_bound(P, neighbors)
 *     if sizeR + bound <= best_size_p[0]:             # <<<<<<<<<<<<<<
 *         return
 *     cdef ull PX = P | X
*/
  }

  /* "solver_c.pyx":42
 *     if sizeR + bound <= best_size_p[0]:
 *         return
 *     cdef ull PX = P | X             # <<<<<<<<<<<<<<
 *     cdef int maxd = -1
 *     cdef idx_t u = 0
*/
  __pyx_v_PX = (__pyx_v_P | __pyx_v_X);

  /* "solver_c.pyx":43
 *         return
 *     cdef ull PX = P | X
 *     cdef int maxd = -1             # <<<<<<<<<<<<<<
 *     cdef idx_t u = 0
 *     cdef ull tmp = PX, v
*/
  __pyx_v_maxd = -1;

  /* "solver_c.pyx":44
 *     cdef ull PX = P | X
 *     cdef int maxd = -1
 *     cdef idx_t u = 0             # <<<<<<<<<<<<<<
 *     cdef ull tmp = PX, v
 *     cdef idx_t i
*/
  __pyx_v_u = 0;

  /* "solver_c.pyx":45
 *     cdef int maxd = -1
 *     cdef idx_t u = 0
 *     cdef ull tmp = PX, v             # <<<<<<<<<<<<<<
 *     cdef idx_t i
 *     cdef int d
*/
  __pyx_v_tmp = __pyx_v_PX;

  /* "solver_c.pyx":48
 *     cdef idx_t i
 *     cdef int d
 *     while tmp:             # <<<<<<<<<<<<<<
 *         v = tmp & -tmp
 *         tmp -= v
*/
  while (1) {
    __pyx_t_2 = (__pyx_v_tmp != 0);
    if (!__pyx_t_2) break;

    /* "solver_c.pyx":49
 *     cdef int d
 *     while tmp:
 *         v = tmp & -tmp             # <<<<<<<<<<<<<<
 *         tmp -= v
 *         i = ctz(v)
*/
    __pyx_v_v = (__pyx_v_tmp & (-__pyx_v_tmp));

    /* "solver_c.pyx":50
 *     while tmp:
 *         v = tmp & -tmp
 *         tmp -= v             # <<<<<<<<<<<<<<
 *         i = ctz(v)
 *         d = bc(P & neighbors[i])
*/
    __pyx_v_tmp = (__pyx_v_tmp - __pyx_v_v);

    /* "solver_c.pyx":51
 *         v = tmp & -tmp
 *         tmp -= v
 *         i = ctz(v)             # <<<<<<<<<<<<<<
 *         d = bc(P & neighbors[i])
 *         if d > maxd:
*/
    __pyx_t_4 = __pyx_f_8solver_c_ctz(__pyx_v_v); if (unlikely(__pyx_t_4 == ((__pyx_t_8solver_c_idx_t)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 51, __pyx_L1_error)
    __pyx_v_i = __pyx_t_4;

    /* "solver_c.pyx":52
 *         tmp -= v
 *         i = ctz(v)
 *         d = bc(P & neighbors[i])             # <<<<<<<<<<<<<<
 *         if d > maxd:
 *             maxd = d
*/
    __pyx_t_1 = __pyx_f_8solver_c_bc((__pyx_v_P & (__pyx_v_neighbors[__pyx_v_i]))); if (unlikely(__pyx_t_1 == ((int)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 52, __pyx_L1_error)
    __pyx_v_d = __pyx_t_1;

    /* "solver_c.pyx":53
 *         i = ctz(v)
 *         d = bc(P & neighbors[i])
 *         if d > maxd:             # <<<<<<<<<<<<<<
 *             maxd = d
 *             u = i
*/
    __pyx_t_2 = (__pyx_v_d > __pyx_v_maxd);
    if (__pyx_t_2) {

      /* "solver_c.pyx":54
 *         d = bc(P & neighbors[i])
 *         if d > maxd:
 *             maxd = d             # <<<<<<<<<<<<<<
 *             u = i
 *     cdef ull ext = P & ~neighbors[u]
*/
      __pyx_v_maxd = __pyx_v_d;

      /* "solver_c.pyx":55
 *         if d > maxd:
 *             maxd = d
 *             u = i             # <<<<<<<<<<<<<<
 *     cdef ull ext = P & ~neighbors[u]
 *     tmp = ext
*/
      __pyx_v_u = __pyx_v_i;

      /* "solver_c.pyx":53
 *         i = ctz(v)
 *         d = bc(P & neighbors[i])
 *         if d > maxd:             # <<<<<<<<<<<<<<
 *             maxd = d
 *             u = i
*/
    }
  }

  /* "solver_c.pyx":56
 *             maxd = d
 *             u = i
 *     cdef ull ext = P & ~neighbors[u]             # <<<<<<<<<<<<<<
 *     tmp = ext
 *     while tmp:
*/
  __pyx_v_ext = (__pyx_v_P & (~(__pyx_v_neighbors[__pyx_v_u])));

  /* "solver_c.pyx":57
 *             u = i
 *     cdef ull ext = P & ~neighbors[u]
 *     tmp = ext             # <<<<<<<<<<<<<<
 *     while tmp:
 *         v = tmp & -tmp
*/
  __pyx_v_tmp = __pyx_v_ext;

  /* "solver_c.pyx":58
 *     cdef ull ext = P & ~neighbors[u]
 *     tmp = ext
 *     while tmp:             # <<<<<<<<<<<<<<
 *         v = tmp & -tmp
 *         tmp -= v
*/
  while (1) {
    __pyx_t_2 = (__pyx_v_tmp != 0);
    if (!__pyx_t_2) break;

    /* "solver_c.pyx":59
 *     tmp = ext
 *     while tmp:
 *         v = tmp & -tmp             # <<<<<<<<<<<<<<
 *         tmp -= v
 *         i = ctz(v)
*/
    __pyx_v_v = (__pyx_v_tmp & (-__pyx_v_tmp));

    /* "solver_c.pyx":60
 *     while tmp:
 *         v = tmp & -tmp
 *         tmp -= v             # <<<<<<<<<<<<<<
 *         i = ctz(v)
 *         bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)
*/
    __pyx_v_tmp = (__pyx_v_tmp - __pyx_v_v);

    /* "solver_c.pyx":61
 *         v = tmp & -tmp
 *         tmp -= v
 *         i = ctz(v)             # <<<<<<<<<<<<<<
 *         bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)
 *         P &= ~v
*/
    __pyx_t_4 = __pyx_f_8solver_c_ctz(__pyx_v_v); if (unlikely(__pyx_t_4 == ((__pyx_t_8solver_c_idx_t)-1) && __Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 61, __pyx_L1_error)
    __pyx_v_i = __pyx_t_4;

    /* "solver_c.pyx":62
 *         tmp -= v
 *         i = ctz(v)
 *         bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)             # <<<<<<<<<<<<<<
 *         P &= ~v
 *         X |= v
*/
    __pyx_f_8solver_c_bronk((__pyx_v_R | __pyx_v_v), (__pyx_v_P & (__pyx_v_neighbors[__pyx_v_i])), (__pyx_v_X & (__pyx_v_neighbors[__pyx_v_i])), __pyx_v_best_size_p, __pyx_v_bestR_p, __pyx_v_neighbors, __pyx_v_n); if (unlikely(__Pyx_ErrOccurredWithGIL())) __PYX_ERR(0, 62, __pyx_L1_error)

    /* "solver_c.pyx":63
 *         i = ctz(v)
 *         bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)
 *         P &= ~v             # <<<<<<<<<<<<<<
 *         X |= v
 * 
*/
    __pyx_v_P = (__pyx_v_P & (~__pyx_v_v));

    /* "solver_c.pyx":64
 *         bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)
 *         P &= ~v
 *         X |= v             # <<<<<<<<<<<<<<
 * 
 * def solve_c(object problem):
*/
    __pyx_v_X = (__pyx_v_X | __pyx_v_v);
  }

  /* "solver_c.pyx":30
 *             cur &= ~neighbors[i]
 *     return color
 * cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:             # <<<<<<<<<<<<<<
 *     cdef int sizeR = bc(R)
 *     if P == 0 and X == 0:
*/

  /* function exit code */
  goto __pyx_L0;
  __pyx_L1_error:;
  __pyx_gilstate_save = __Pyx_PyGILState_Ensure();
  __Pyx_AddTraceback("solver_c.bronk", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __Pyx_PyGILState_Release(__pyx_gilstate_save);
  __pyx_L0:;
}

/* "solver_c.pyx":66
 *         X |= v
 * 
 * def solve_c(object problem):             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
*/

/* Python wrapper */
static PyObject *__pyx_pw_8solver_c_1solve_c(PyObject *__pyx_self, 
#if CYTHON_METH_FASTCALL
PyObject *const *__pyx_args, Py_ssize_t __pyx_nargs, PyObject *__pyx_kwds
#else
PyObject *__pyx_args, PyObject *__pyx_kwds
#endif
); /*proto*/
static PyMethodDef __pyx_mdef_8solver_c_1solve_c = {"solve_c", (PyCFunction)(void(*)(void))(__Pyx_PyCFunction_FastCallWithKeywords)__pyx_pw_8solver_c_1solve_c, __Pyx_METH_FASTCALL|METH_KEYWORDS, 0};
static PyObject *__pyx_pw_8solver_c_1solve_c(PyObject *__pyx_self, 
#if CYTHON_METH_FASTCALL
PyObject *const *__pyx_args, Py_ssize_t __pyx_nargs, PyObject *__pyx_kwds
#else
PyObject *__pyx_args, PyObject *__pyx_kwds
#endif
) {
  PyObject *__pyx_v_problem = 0;
  #if !CYTHON_METH_FASTCALL
  CYTHON_UNUSED Py_ssize_t __pyx_nargs;
  #endif
  CYTHON_UNUSED PyObject *const *__pyx_kwvalues;
  PyObject* values[1] = {0};
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  PyObject *__pyx_r = 0;
  __Pyx_RefNannyDeclarations
  __Pyx_RefNannySetupContext("solve_c (wrapper)", 0);
  #if !CYTHON_METH_FASTCALL
  #if CYTHON_ASSUME_SAFE_SIZE
  __pyx_nargs = PyTuple_GET_SIZE(__pyx_args);
  #else
  __pyx_nargs = PyTuple_Size(__pyx_args); if (unlikely(__pyx_nargs < 0)) return NULL;
  #endif
  #endif
  __pyx_kwvalues = __Pyx_KwValues_FASTCALL(__pyx_args, __pyx_nargs);
  {
    PyObject ** const __pyx_pyargnames[] = {&__pyx_mstate_global->__pyx_n_u_problem,0};
    const Py_ssize_t __pyx_kwds_len = (__pyx_kwds) ? __Pyx_NumKwargs_FASTCALL(__pyx_kwds) : 0;
    if (unlikely(__pyx_kwds_len) < 0) __PYX_ERR(0, 66, __pyx_L3_error)
    if (__pyx_kwds_len > 0) {
      switch (__pyx_nargs) {
        case  1:
        values[0] = __Pyx_ArgRef_FASTCALL(__pyx_args, 0);
        if (!CYTHON_ASSUME_SAFE_MACROS && unlikely(!values[0])) __PYX_ERR(0, 66, __pyx_L3_error)
        CYTHON_FALLTHROUGH;
        case  0: break;
        default: goto __pyx_L5_argtuple_error;
      }
      const Py_ssize_t kwd_pos_args = __pyx_nargs;
      if (__Pyx_ParseKeywords(__pyx_kwds, __pyx_kwvalues, __pyx_pyargnames, 0, values, kwd_pos_args, __pyx_kwds_len, "solve_c", 0) < 0) __PYX_ERR(0, 66, __pyx_L3_error)
      for (Py_ssize_t i = __pyx_nargs; i < 1; i++) {
        if (unlikely(!values[i])) { __Pyx_RaiseArgtupleInvalid("solve_c", 1, 1, 1, i); __PYX_ERR(0, 66, __pyx_L3_error) }
      }
    } else if (unlikely(__pyx_nargs != 1)) {
      goto __pyx_L5_argtuple_error;
    } else {
      values[0] = __Pyx_ArgRef_FASTCALL(__pyx_args, 0);
      if (!CYTHON_ASSUME_SAFE_MACROS && unlikely(!values[0])) __PYX_ERR(0, 66, __pyx_L3_error)
    }
    __pyx_v_problem = values[0];
  }
  goto __pyx_L6_skip;
  __pyx_L5_argtuple_error:;
  __Pyx_RaiseArgtupleInvalid("solve_c", 1, 1, 1, __pyx_nargs); __PYX_ERR(0, 66, __pyx_L3_error)
  __pyx_L6_skip:;
  goto __pyx_L4_argument_unpacking_done;
  __pyx_L3_error:;
  for (Py_ssize_t __pyx_temp=0; __pyx_temp < (Py_ssize_t)(sizeof(values)/sizeof(values[0])); ++__pyx_temp) {
    Py_XDECREF(values[__pyx_temp]);
  }
  __Pyx_AddTraceback("solver_c.solve_c", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __Pyx_RefNannyFinishContext();
  return NULL;
  __pyx_L4_argument_unpacking_done:;
  __pyx_r = __pyx_pf_8solver_c_solve_c(__pyx_self, __pyx_v_problem);

  /* function exit code */
  for (Py_ssize_t __pyx_temp=0; __pyx_temp < (Py_ssize_t)(sizeof(values)/sizeof(values[0])); ++__pyx_temp) {
    Py_XDECREF(values[__pyx_temp]);
  }
  __Pyx_RefNannyFinishContext();
  return __pyx_r;
}

/* "solver_c.pyx":86
 *     # greedy lower bound
 *     cdef list order = list(range(n))
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())             # <<<<<<<<<<<<<<
 *     cdef ull R0 = 0
 *     for i in order:
*/

/* Python wrapper */
static PyObject *__pyx_pw_8solver_c_7solve_c_lambda(PyObject *__pyx_self, 
#if CYTHON_METH_FASTCALL
PyObject *const *__pyx_args, Py_ssize_t __pyx_nargs, PyObject *__pyx_kwds
#else
PyObject *__pyx_args, PyObject *__pyx_kwds
#endif
); /*proto*/
static PyMethodDef __pyx_mdef_8solver_c_7solve_c_lambda = {"lambda", (PyCFunction)(void(*)(void))(__Pyx_PyCFunction_FastCallWithKeywords)__pyx_pw_8solver_c_7solve_c_lambda, __Pyx_METH_FASTCALL|METH_KEYWORDS, 0};
static PyObject *__pyx_pw_8solver_c_7solve_c_lambda(PyObject *__pyx_self, 
#if CYTHON_METH_FASTCALL
PyObject *const *__pyx_args, Py_ssize_t __pyx_nargs, PyObject *__pyx_kwds
#else
PyObject *__pyx_args, PyObject *__pyx_kwds
#endif
) {
  PyObject *__pyx_v_x = 0;
  #if !CYTHON_METH_FASTCALL
  CYTHON_UNUSED Py_ssize_t __pyx_nargs;
  #endif
  CYTHON_UNUSED PyObject *const *__pyx_kwvalues;
  PyObject* values[1] = {0};
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  PyObject *__pyx_r = 0;
  __Pyx_RefNannyDeclarations
  __Pyx_RefNannySetupContext("lambda (wrapper)", 0);
  #if !CYTHON_METH_FASTCALL
  #if CYTHON_ASSUME_SAFE_SIZE
  __pyx_nargs = PyTuple_GET_SIZE(__pyx_args);
  #else
  __pyx_nargs = PyTuple_Size(__pyx_args); if (unlikely(__pyx_nargs < 0)) return NULL;
  #endif
  #endif
  __pyx_kwvalues = __Pyx_KwValues_FASTCALL(__pyx_args, __pyx_nargs);
  {
    PyObject ** const __pyx_pyargnames[] = {&__pyx_mstate_global->__pyx_n_u_x,0};
    const Py_ssize_t __pyx_kwds_len = (__pyx_kwds) ? __Pyx_NumKwargs_FASTCALL(__pyx_kwds) : 0;
    if (unlikely(__pyx_kwds_len) < 0) __PYX_ERR(0, 86, __pyx_L3_error)
    if (__pyx_kwds_len > 0) {
      switch (__pyx_nargs) {
        case  1:
        values[0] = __Pyx_ArgRef_FASTCALL(__pyx_args, 0);
        if (!CYTHON_ASSUME_SAFE_MACROS && unlikely(!values[0])) __PYX_ERR(0, 86, __pyx_L3_error)
        CYTHON_FALLTHROUGH;
        case  0: break;
        default: goto __pyx_L5_argtuple_error;
      }
      const Py_ssize_t kwd_pos_args = __pyx_nargs;
      if (__Pyx_ParseKeywords(__pyx_kwds, __pyx_kwvalues, __pyx_pyargnames, 0, values, kwd_pos_args, __pyx_kwds_len, "lambda", 0) < 0) __PYX_ERR(0, 86, __pyx_L3_error)
      for (Py_ssize_t i = __pyx_nargs; i < 1; i++) {
        if (unlikely(!values[i])) { __Pyx_RaiseArgtupleInvalid("lambda", 1, 1, 1, i); __PYX_ERR(0, 86, __pyx_L3_error) }
      }
    } else if (unlikely(__pyx_nargs != 1)) {
      goto __pyx_L5_argtuple_error;
    } else {
      values[0] = __Pyx_ArgRef_FASTCALL(__pyx_args, 0);
      if (!CYTHON_ASSUME_SAFE_MACROS && unlikely(!values[0])) __PYX_ERR(0, 86, __pyx_L3_error)
    }
    __pyx_v_x = values[0];
  }
  goto __pyx_L6_skip;
  __pyx_L5_argtuple_error:;
  __Pyx_RaiseArgtupleInvalid("lambda", 1, 1, 1, __pyx_nargs); __PYX_ERR(0, 86, __pyx_L3_error)
  __pyx_L6_skip:;
  goto __pyx_L4_argument_unpacking_done;
  __pyx_L3_error:;
  for (Py_ssize_t __pyx_temp=0; __pyx_temp < (Py_ssize_t)(sizeof(values)/sizeof(values[0])); ++__pyx_temp) {
    Py_XDECREF(values[__pyx_temp]);
  }
  __Pyx_AddTraceback("solver_c.solve_c.lambda", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __Pyx_RefNannyFinishContext();
  return NULL;
  __pyx_L4_argument_unpacking_done:;
  __pyx_r = __pyx_lambda_funcdef_lambda(__pyx_self, __pyx_v_x);

  /* function exit code */
  for (Py_ssize_t __pyx_temp=0; __pyx_temp < (Py_ssize_t)(sizeof(values)/sizeof(values[0])); ++__pyx_temp) {
    Py_XDECREF(values[__pyx_temp]);
  }
  __Pyx_RefNannyFinishContext();
  return __pyx_r;
}

static PyObject *__pyx_lambda_funcdef_lambda(PyObject *__pyx_self, PyObject *__pyx_v_x) {
  struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *__pyx_cur_scope;
  struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *__pyx_outer_scope;
  PyObject *__pyx_r = NULL;
  __Pyx_RefNannyDeclarations
  PyObject *__pyx_t_1 = NULL;
  PyObject *__pyx_t_2 = NULL;
  Py_ssize_t __pyx_t_3;
  PyObject *__pyx_t_4 = NULL;
  size_t __pyx_t_5;
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  __Pyx_RefNannySetupContext("lambda", 0);
  __pyx_outer_scope = (struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *) __Pyx_CyFunction_GetClosure(__pyx_self);
  __pyx_cur_scope = __pyx_outer_scope;
  __Pyx_XDECREF(__pyx_r);
  __pyx_t_3 = __Pyx_PyIndex_AsSsize_t(__pyx_v_x); if (unlikely((__pyx_t_3 == (Py_ssize_t)-1) && PyErr_Occurred())) __PYX_ERR(0, 86, __pyx_L1_error)
  __pyx_t_4 = __Pyx_PyLong_From_unsigned_PY_LONG_LONG((__pyx_cur_scope->__pyx_v_neighbors[__pyx_t_3])); if (unlikely(!__pyx_t_4)) __PYX_ERR(0, 86, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_4);
  __pyx_t_2 = __pyx_t_4;
  __Pyx_INCREF(__pyx_t_2);
  __pyx_t_5 = 0;
  {
    PyObject *__pyx_callargs[2] = {__pyx_t_2, NULL};
    __pyx_t_1 = __Pyx_PyObject_FastCallMethod(__pyx_mstate_global->__pyx_n_u_bit_count, __pyx_callargs+__pyx_t_5, (1-__pyx_t_5) | (1*__Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET));
    __Pyx_XDECREF(__pyx_t_2); __pyx_t_2 = 0;
    __Pyx_DECREF(__pyx_t_4); __pyx_t_4 = 0;
    if (unlikely(!__pyx_t_1)) __PYX_ERR(0, 86, __pyx_L1_error)
    __Pyx_GOTREF(__pyx_t_1);
  }
  __pyx_r = __pyx_t_1;
  __pyx_t_1 = 0;
  goto __pyx_L0;

  /* function exit code */
  __pyx_L1_error:;
  __Pyx_XDECREF(__pyx_t_1);
  __Pyx_XDECREF(__pyx_t_2);
  __Pyx_XDECREF(__pyx_t_4);
  __Pyx_AddTraceback("solver_c.solve_c.lambda", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __pyx_r = NULL;
  __pyx_L0:;
  __Pyx_XGIVEREF(__pyx_r);
  __Pyx_RefNannyFinishContext();
  return __pyx_r;
}

/* "solver_c.pyx":66
 *         X |= v
 * 
 * def solve_c(object problem):             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
*/

static PyObject *__pyx_pf_8solver_c_solve_c(CYTHON_UNUSED PyObject *__pyx_self, PyObject *__pyx_v_problem) {
  struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *__pyx_cur_scope;
  Py_ssize_t __pyx_v_n;
  Py_ssize_t __pyx_v_i;
  Py_ssize_t __pyx_v_j;
  __pyx_t_8solver_c_ull __pyx_v_mask;
  __pyx_t_8solver_c_ull __pyx_v_full;
  int __pyx_v_best_size;
  __pyx_t_8solver_c_ull __pyx_v_bestR;
  int *__pyx_v_best_size_p;
  __pyx_t_8solver_c_ull *__pyx_v_bestR_p;
  PyObject *__pyx_v_order = 0;
  __pyx_t_8solver_c_ull __pyx_v_R0;
  PyObject *__pyx_v_res = 0;
  PyObject *__pyx_r = NULL;
  __Pyx_RefNannyDeclarations
  Py_ssize_t __pyx_t_1;
  Py_ssize_t __pyx_t_2;
  Py_ssize_t __pyx_t_3;
  Py_ssize_t __pyx_t_4;
  Py_ssize_t __pyx_t_5;
  Py_ssize_t __pyx_t_6;
  PyObject *__pyx_t_7 = NULL;
  PyObject *__pyx_t_8 = NULL;
  int __pyx_t_9;
  int __pyx_t_10;
  PyObject *__pyx_t_11 = NULL;
  PyObject *__pyx_t_12 = NULL;
  size_t __pyx_t_13;
  int __pyx_t_14;
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  __Pyx_RefNannySetupContext("solve_c", 0);
  __pyx_cur_scope = (struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *)__pyx_tp_new_8solver_c___pyx_scope_struct__solve_c(__pyx_mstate_global->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c, __pyx_mstate_global->__pyx_empty_tuple, NULL);
  if (unlikely(!__pyx_cur_scope)) {
    __pyx_cur_scope = ((struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *)Py_None);
    __Pyx_INCREF(Py_None);
    __PYX_ERR(0, 66, __pyx_L1_error)
  } else {
    __Pyx_GOTREF((PyObject *)__pyx_cur_scope);
  }

  /* "solver_c.pyx":67
 * 
 * def solve_c(object problem):
 *     cdef Py_ssize_t n = len(problem)             # <<<<<<<<<<<<<<
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
 *     cdef Py_ssize_t i, j
*/
  __pyx_t_1 = PyObject_Length(__pyx_v_problem); if (unlikely(__pyx_t_1 == ((Py_ssize_t)-1))) __PYX_ERR(0, 67, __pyx_L1_error)
  __pyx_v_n = __pyx_t_1;

  /* "solver_c.pyx":68
 * def solve_c(object problem):
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t i, j
 *     cdef ull mask, full
*/
  __pyx_cur_scope->__pyx_v_neighbors = ((__pyx_t_8solver_c_ull *)PyMem_Malloc((__pyx_v_n * (sizeof(__pyx_t_8solver_c_ull)))));

  /* "solver_c.pyx":73
 *     cdef int best_size
 *     cdef ull bestR
 *     cdef int* best_size_p = &best_size             # <<<<<<<<<<<<<<
 *     cdef ull* bestR_p = &bestR
 * 
*/
  __pyx_v_best_size_p = (&__pyx_v_best_size);

  /* "solver_c.pyx":74
 *     cdef ull bestR
 *     cdef int* best_size_p = &best_size
 *     cdef ull* bestR_p = &bestR             # <<<<<<<<<<<<<<
 * 
 *     full = (<ull>1 << n) - 1
*/
  __pyx_v_bestR_p = (&__pyx_v_bestR);

  /* "solver_c.pyx":76
 *     cdef ull* bestR_p = &bestR
 * 
 *     full = (<ull>1 << n) - 1             # <<<<<<<<<<<<<<
 *     for i in range(n):
 *         mask = full & ~(<ull>1 << i)
*/
  __pyx_v_full = ((((__pyx_t_8solver_c_ull)1) << __pyx_v_n) - 1);

  /* "solver_c.pyx":77
 * 
 *     full = (<ull>1 << n) - 1
 *     for i in range(n):             # <<<<<<<<<<<<<<
 *         mask = full & ~(<ull>1 << i)
 *         for j in range(n):
*/
  __pyx_t_1 = __pyx_v_n;
  __pyx_t_2 = __pyx_t_1;
  for (__pyx_t_3 = 0; __pyx_t_3 < __pyx_t_2; __pyx_t_3+=1) {
    __pyx_v_i = __pyx_t_3;

    /* "solver_c.pyx":78
 *     full = (<ull>1 << n) - 1
 *     for i in range(n):
 *         mask = full & ~(<ull>1 << i)             # <<<<<<<<<<<<<<
 *         for j in range(n):
 *             if (<int>problem[i][j]):
*/
    __pyx_v_mask = (__pyx_v_full & (~(((__pyx_t_8solver_c_ull)1) << __pyx_v_i)));

    /* "solver_c.pyx":79
 *     for i in range(n):
 *         mask = full & ~(<ull>1 << i)
 *         for j in range(n):             # <<<<<<<<<<<<<<
 *             if (<int>problem[i][j]):
 *                 mask &= ~(<ull>1 << j)
*/
    __pyx_t_4 = __pyx_v_n;
    __pyx_t_5 = __pyx_t_4;
    for (__pyx_t_6 = 0; __pyx_t_6 < __pyx_t_5; __pyx_t_6+=1) {
      __pyx_v_j = __pyx_t_6;

      /* "solver_c.pyx":80
 *         mask = full & ~(<ull>1 << i)
 *         for j in range(n):
 *             if (<int>problem[i][j]):             # <<<<<<<<<<<<<<
 *                 mask &= ~(<ull>1 << j)
 *         neighbors[i] = mask
*/
      __pyx_t_7 = __Pyx_GetItemInt(__pyx_v_problem, __pyx_v_i, Py_ssize_t, 1, PyLong_FromSsize_t, 0, 0, 0, 1); if (unlikely(!__pyx_t_7)) __PYX_ERR(0, 80, __pyx_L1_error)
      __Pyx_GOTREF(__pyx_t_7);
      __pyx_t_8 = __Pyx_GetItemInt(__pyx_t_7, __pyx_v_j, Py_ssize_t, 1, PyLong_FromSsize_t, 0, 0, 0, 1); if (unlikely(!__pyx_t_8)) __PYX_ERR(0, 80, __pyx_L1_error)
      __Pyx_GOTREF(__pyx_t_8);
      __Pyx_DECREF(__pyx_t_7); __pyx_t_7 = 0;
      __pyx_t_9 = __Pyx_PyLong_As_int(__pyx_t_8); if (unlikely((__pyx_t_9 == (int)-1) && PyErr_Occurred())) __PYX_ERR(0, 80, __pyx_L1_error)
      __Pyx_DECREF(__pyx_t_8); __pyx_t_8 = 0;
      __pyx_t_10 = (((int)__pyx_t_9) != 0);
      if (__pyx_t_10) {

        /* "solver_c.pyx":81
 *         for j in range(n):
 *             if (<int>problem[i][j]):
 *                 mask &= ~(<ull>1 << j)             # <<<<<<<<<<<<<<
 *         neighbors[i] = mask
 * 
*/
        __pyx_v_mask = (__pyx_v_mask & (~(((__pyx_t_8solver_c_ull)1) << __pyx_v_j)));

        /* "solver_c.pyx":80
 *         mask = full & ~(<ull>1 << i)
 *         for j in range(n):
 *             if (<int>problem[i][j]):             # <<<<<<<<<<<<<<
 *                 mask &= ~(<ull>1 << j)
 *         neighbors[i] = mask
*/
      }
    }

    /* "solver_c.pyx":82
 *             if (<int>problem[i][j]):
 *                 mask &= ~(<ull>1 << j)
 *         neighbors[i] = mask             # <<<<<<<<<<<<<<
 * 
 *     # greedy lower bound
*/
    (__pyx_cur_scope->__pyx_v_neighbors[__pyx_v_i]) = __pyx_v_mask;
  }

  /* "solver_c.pyx":85
 * 
 *     # greedy lower bound
 *     cdef list order = list(range(n))             # <<<<<<<<<<<<<<
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())
 *     cdef ull R0 = 0
*/
  __pyx_t_7 = NULL;
  __Pyx_INCREF(__pyx_builtin_range);
  __pyx_t_11 = __pyx_builtin_range; 
  __pyx_t_12 = PyLong_FromSsize_t(__pyx_v_n); if (unlikely(!__pyx_t_12)) __PYX_ERR(0, 85, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_12);
  __pyx_t_13 = 1;
  {
    PyObject *__pyx_callargs[2] = {__pyx_t_7, __pyx_t_12};
    __pyx_t_8 = __Pyx_PyObject_FastCall(__pyx_t_11, __pyx_callargs+__pyx_t_13, (2-__pyx_t_13) | (__pyx_t_13*__Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET));
    __Pyx_XDECREF(__pyx_t_7); __pyx_t_7 = 0;
    __Pyx_DECREF(__pyx_t_12); __pyx_t_12 = 0;
    __Pyx_DECREF(__pyx_t_11); __pyx_t_11 = 0;
    if (unlikely(!__pyx_t_8)) __PYX_ERR(0, 85, __pyx_L1_error)
    __Pyx_GOTREF(__pyx_t_8);
  }
  __pyx_t_11 = __Pyx_PySequence_ListKeepNew(__pyx_t_8); if (unlikely(!__pyx_t_11)) __PYX_ERR(0, 85, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_11);
  __Pyx_DECREF(__pyx_t_8); __pyx_t_8 = 0;
  __pyx_v_order = ((PyObject*)__pyx_t_11);
  __pyx_t_11 = 0;

  /* "solver_c.pyx":86
 *     # greedy lower bound
 *     cdef list order = list(range(n))
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())             # <<<<<<<<<<<<<<
 *     cdef ull R0 = 0
 *     for i in order:
*/
  __pyx_t_8 = __pyx_v_order;
  __Pyx_INCREF(__pyx_t_8);
  __pyx_t_12 = __Pyx_CyFunction_New(&__pyx_mdef_8solver_c_7solve_c_lambda, 0, __pyx_mstate_global->__pyx_n_u_solve_c_locals_lambda, ((PyObject*)__pyx_cur_scope), __pyx_mstate_global->__pyx_n_u_solver_c, __pyx_mstate_global->__pyx_d, ((PyObject *)__pyx_mstate_global->__pyx_codeobj_tab[0])); if (unlikely(!__pyx_t_12)) __PYX_ERR(0, 86, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_12);
  __pyx_t_13 = 0;
  {
    PyObject *__pyx_callargs[2 + ((CYTHON_VECTORCALL) ? 1 : 0)] = {__pyx_t_8, NULL};
    __pyx_t_7 = __Pyx_MakeVectorcallBuilderKwds(1); if (unlikely(!__pyx_t_7)) __PYX_ERR(0, 86, __pyx_L1_error)
    __Pyx_GOTREF(__pyx_t_7);
    if (__Pyx_VectorcallBuilder_AddArg(__pyx_mstate_global->__pyx_n_u_key, __pyx_t_12, __pyx_t_7, __pyx_callargs+1, 0) < 0) __PYX_ERR(0, 86, __pyx_L1_error)
    __pyx_t_11 = __Pyx_Object_VectorcallMethod_CallFromBuilder(__pyx_mstate_global->__pyx_n_u_sort, __pyx_callargs+__pyx_t_13, (1-__pyx_t_13) | (1*__Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET), __pyx_t_7);
    __Pyx_XDECREF(__pyx_t_8); __pyx_t_8 = 0;
    __Pyx_DECREF(__pyx_t_12); __pyx_t_12 = 0;
    __Pyx_DECREF(__pyx_t_7); __pyx_t_7 = 0;
    if (unlikely(!__pyx_t_11)) __PYX_ERR(0, 86, __pyx_L1_error)
    __Pyx_GOTREF(__pyx_t_11);
  }
  __Pyx_DECREF(__pyx_t_11); __pyx_t_11 = 0;

  /* "solver_c.pyx":87
 *     cdef list order = list(range(n))
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())
 *     cdef ull R0 = 0             # <<<<<<<<<<<<<<
 *     for i in order:
 *         if (R0 & neighbors[i]) == R0:
*/
  __pyx_v_R0 = 0;

  /* "solver_c.pyx":88
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())
 *     cdef ull R0 = 0
 *     for i in order:             # <<<<<<<<<<<<<<
 *         if (R0 & neighbors[i]) == R0:
 *             R0 |= (<ull>1 << i)
*/
  __pyx_t_11 = __pyx_v_order; __Pyx_INCREF(__pyx_t_11);
  __pyx_t_1 = 0;
  for (;;) {
    {
      Py_ssize_t __pyx_temp = __Pyx_PyList_GET_SIZE(__pyx_t_11);
      #if !CYTHON_ASSUME_SAFE_SIZE
      if (unlikely((__pyx_temp < 0))) __PYX_ERR(0, 88, __pyx_L1_error)
      #endif
      if (__pyx_t_1 >= __pyx_temp) break;
    }
    __pyx_t_7 = __Pyx_PyList_GetItemRef(__pyx_t_11, __pyx_t_1);
    ++__pyx_t_1;
    if (unlikely(!__pyx_t_7)) __PYX_ERR(0, 88, __pyx_L1_error)
    __Pyx_GOTREF(__pyx_t_7);
    __pyx_t_2 = __Pyx_PyIndex_AsSsize_t(__pyx_t_7); if (unlikely((__pyx_t_2 == (Py_ssize_t)-1) && PyErr_Occurred())) __PYX_ERR(0, 88, __pyx_L1_error)
    __Pyx_DECREF(__pyx_t_7); __pyx_t_7 = 0;
    __pyx_v_i = __pyx_t_2;

    /* "solver_c.pyx":89
 *     cdef ull R0 = 0
 *     for i in order:
 *         if (R0 & neighbors[i]) == R0:             # <<<<<<<<<<<<<<
 *             R0 |= (<ull>1 << i)
 * 
*/
    __pyx_t_10 = ((__pyx_v_R0 & (__pyx_cur_scope->__pyx_v_neighbors[__pyx_v_i])) == __pyx_v_R0);
    if (__pyx_t_10) {

      /* "solver_c.pyx":90
 *     for i in order:
 *         if (R0 & neighbors[i]) == R0:
 *             R0 |= (<ull>1 << i)             # <<<<<<<<<<<<<<
 * 
 *     best_size = bc(R0)
*/
      __pyx_v_R0 = (__pyx_v_R0 | (((__pyx_t_8solver_c_ull)1) << __pyx_v_i));

      /* "solver_c.pyx":89
 *     cdef ull R0 = 0
 *     for i in order:
 *         if (R0 & neighbors[i]) == R0:             # <<<<<<<<<<<<<<
 *             R0 |= (<ull>1 << i)
 * 
*/
    }

    /* "solver_c.pyx":88
 *     order.sort(key=lambda x: (neighbors[x]).bit_count())
 *     cdef ull R0 = 0
 *     for i in order:             # <<<<<<<<<<<<<<
 *         if (R0 & neighbors[i]) == R0:
 *             R0 |= (<ull>1 << i)
*/
  }
  __Pyx_DECREF(__pyx_t_11); __pyx_t_11 = 0;

  /* "solver_c.pyx":92
 *             R0 |= (<ull>1 << i)
 * 
 *     best_size = bc(R0)             # <<<<<<<<<<<<<<
 *     bestR = R0
 * 
*/
  __pyx_t_9 = __pyx_f_8solver_c_bc(__pyx_v_R0); if (unlikely(__pyx_t_9 == ((int)-1) && PyErr_Occurred())) __PYX_ERR(0, 92, __pyx_L1_error)
  __pyx_v_best_size = __pyx_t_9;

  /* "solver_c.pyx":93
 * 
 *     best_size = bc(R0)
 *     bestR = R0             # <<<<<<<<<<<<<<
 * 
 *     bronk(<ull>0, full, <ull>0, best_size_p, bestR_p, neighbors, <idx_t>n)
*/
  __pyx_v_bestR = __pyx_v_R0;

  /* "solver_c.pyx":95
 *     bestR = R0
 * 
 *     bronk(<ull>0, full, <ull>0, best_size_p, bestR_p, neighbors, <idx_t>n)             # <<<<<<<<<<<<<<
 * 
 *     # extract result
*/
  __pyx_f_8solver_c_bronk(((__pyx_t_8solver_c_ull)0), __pyx_v_full, ((__pyx_t_8solver_c_ull)0), __pyx_v_best_size_p, __pyx_v_bestR_p, __pyx_cur_scope->__pyx_v_neighbors, ((__pyx_t_8solver_c_idx_t)__pyx_v_n)); if (unlikely(PyErr_Occurred())) __PYX_ERR(0, 95, __pyx_L1_error)

  /* "solver_c.pyx":98
 * 
 *     # extract result
 *     cdef list res = []             # <<<<<<<<<<<<<<
 *     for i in range(n):
 *         if (bestR >> i) & 1:
*/
  __pyx_t_11 = PyList_New(0); if (unlikely(!__pyx_t_11)) __PYX_ERR(0, 98, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_11);
  __pyx_v_res = ((PyObject*)__pyx_t_11);
  __pyx_t_11 = 0;

  /* "solver_c.pyx":99
 *     # extract result
 *     cdef list res = []
 *     for i in range(n):             # <<<<<<<<<<<<<<
 *         if (bestR >> i) & 1:
 *             res.append(i)
*/
  __pyx_t_1 = __pyx_v_n;
  __pyx_t_2 = __pyx_t_1;
  for (__pyx_t_3 = 0; __pyx_t_3 < __pyx_t_2; __pyx_t_3+=1) {
    __pyx_v_i = __pyx_t_3;

    /* "solver_c.pyx":100
 *     cdef list res = []
 *     for i in range(n):
 *         if (bestR >> i) & 1:             # <<<<<<<<<<<<<<
 *             res.append(i)
 * 
*/
    __pyx_t_10 = (((__pyx_v_bestR >> __pyx_v_i) & 1) != 0);
    if (__pyx_t_10) {

      /* "solver_c.pyx":101
 *     for i in range(n):
 *         if (bestR >> i) & 1:
 *             res.append(i)             # <<<<<<<<<<<<<<
 * 
 *     PyMem_Free(neighbors)
*/
      __pyx_t_11 = PyLong_FromSsize_t(__pyx_v_i); if (unlikely(!__pyx_t_11)) __PYX_ERR(0, 101, __pyx_L1_error)
      __Pyx_GOTREF(__pyx_t_11);
      __pyx_t_14 = __Pyx_PyList_Append(__pyx_v_res, __pyx_t_11); if (unlikely(__pyx_t_14 == ((int)-1))) __PYX_ERR(0, 101, __pyx_L1_error)
      __Pyx_DECREF(__pyx_t_11); __pyx_t_11 = 0;

      /* "solver_c.pyx":100
 *     cdef list res = []
 *     for i in range(n):
 *         if (bestR >> i) & 1:             # <<<<<<<<<<<<<<
 *             res.append(i)
 * 
*/
    }
  }

  /* "solver_c.pyx":103
 *             res.append(i)
 * 
 *     PyMem_Free(neighbors)             # <<<<<<<<<<<<<<
 *     return res
*/
  PyMem_Free(__pyx_cur_scope->__pyx_v_neighbors);

  /* "solver_c.pyx":104
 * 
 *     PyMem_Free(neighbors)
 *     return res             # <<<<<<<<<<<<<<
*/
  __Pyx_XDECREF(__pyx_r);
  __Pyx_INCREF(__pyx_v_res);
  __pyx_r = __pyx_v_res;
  goto __pyx_L0;

  /* "solver_c.pyx":66
 *         X |= v
 * 
 * def solve_c(object problem):             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
*/

  /* function exit code */
  __pyx_L1_error:;
  __Pyx_XDECREF(__pyx_t_7);
  __Pyx_XDECREF(__pyx_t_8);
  __Pyx_XDECREF(__pyx_t_11);
  __Pyx_XDECREF(__pyx_t_12);
  __Pyx_AddTraceback("solver_c.solve_c", __pyx_clineno, __pyx_lineno, __pyx_filename);
  __pyx_r = NULL;
  __pyx_L0:;
  __Pyx_XDECREF(__pyx_v_order);
  __Pyx_XDECREF(__pyx_v_res);
  __Pyx_DECREF((PyObject *)__pyx_cur_scope);
  __Pyx_XGIVEREF(__pyx_r);
  __Pyx_RefNannyFinishContext();
  return __pyx_r;
}
/* #### Code section: module_exttypes ### */

static PyObject *__pyx_tp_new_8solver_c___pyx_scope_struct__solve_c(PyTypeObject *t, CYTHON_UNUSED PyObject *a, CYTHON_UNUSED PyObject *k) {
  PyObject *o;
  #if CYTHON_COMPILING_IN_LIMITED_API
  allocfunc alloc_func = (allocfunc)PyType_GetSlot(t, Py_tp_alloc);
  o = alloc_func(t, 0);
  #else
  #if CYTHON_USE_FREELISTS
  if (likely((int)(__pyx_mstate_global->__pyx_freecount_8solver_c___pyx_scope_struct__solve_c > 0) & (int)(t->tp_basicsize == sizeof(struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c)))) {
    o = (PyObject*)__pyx_mstate_global->__pyx_freelist_8solver_c___pyx_scope_struct__solve_c[--__pyx_mstate_global->__pyx_freecount_8solver_c___pyx_scope_struct__solve_c];
    memset(o, 0, sizeof(struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c));
    (void) PyObject_INIT(o, t);
  } else
  #endif
  {
    o = (*t->tp_alloc)(t, 0);
    if (unlikely(!o)) return 0;
  }
  #endif
  return o;
}

static void __pyx_tp_dealloc_8solver_c___pyx_scope_struct__solve_c(PyObject *o) {
  #if CYTHON_USE_TP_FINALIZE
  if (unlikely((PY_VERSION_HEX >= 0x03080000 || __Pyx_PyType_HasFeature(Py_TYPE(o), Py_TPFLAGS_HAVE_FINALIZE)) && __Pyx_PyObject_GetSlot(o, tp_finalize, destructor)) && (!PyType_IS_GC(Py_TYPE(o)) || !__Pyx_PyObject_GC_IsFinalized(o))) {
    if (__Pyx_PyObject_GetSlot(o, tp_dealloc, destructor) == __pyx_tp_dealloc_8solver_c___pyx_scope_struct__solve_c) {
      if (PyObject_CallFinalizerFromDealloc(o)) return;
    }
  }
  #endif
  #if CYTHON_USE_FREELISTS
  if (((int)(__pyx_mstate_global->__pyx_freecount_8solver_c___pyx_scope_struct__solve_c < 8) & (int)(Py_TYPE(o)->tp_basicsize == sizeof(struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c)))) {
    __pyx_mstate_global->__pyx_freelist_8solver_c___pyx_scope_struct__solve_c[__pyx_mstate_global->__pyx_freecount_8solver_c___pyx_scope_struct__solve_c++] = ((struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c *)o);
  } else
  #endif
  {
    #if CYTHON_USE_TYPE_SLOTS
    (*Py_TYPE(o)->tp_free)(o);
    #else
    {
      freefunc tp_free = (freefunc)PyType_GetSlot(Py_TYPE(o), Py_tp_free);
      if (tp_free) tp_free(o);
    }
    #endif
  }
}
#if CYTHON_USE_TYPE_SPECS
static PyType_Slot __pyx_type_8solver_c___pyx_scope_struct__solve_c_slots[] = {
  {Py_tp_dealloc, (void *)__pyx_tp_dealloc_8solver_c___pyx_scope_struct__solve_c},
  {Py_tp_new, (void *)__pyx_tp_new_8solver_c___pyx_scope_struct__solve_c},
  {0, 0},
};
static PyType_Spec __pyx_type_8solver_c___pyx_scope_struct__solve_c_spec = {
  "solver_c.__pyx_scope_struct__solve_c",
  sizeof(struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c),
  0,
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_VERSION_TAG|Py_TPFLAGS_CHECKTYPES|Py_TPFLAGS_HAVE_NEWBUFFER|Py_TPFLAGS_HAVE_FINALIZE,
  __pyx_type_8solver_c___pyx_scope_struct__solve_c_slots,
};
#else

static PyTypeObject __pyx_type_8solver_c___pyx_scope_struct__solve_c = {
  PyVarObject_HEAD_INIT(0, 0)
  "solver_c.""__pyx_scope_struct__solve_c", /*tp_name*/
  sizeof(struct __pyx_obj_8solver_c___pyx_scope_struct__solve_c), /*tp_basicsize*/
  0, /*tp_itemsize*/
  __pyx_tp_dealloc_8solver_c___pyx_scope_struct__solve_c, /*tp_dealloc*/
  #if PY_VERSION_HEX < 0x030800b4
  0, /*tp_print*/
  #endif
  #if PY_VERSION_HEX >= 0x030800b4
  0, /*tp_vectorcall_offset*/
  #endif
  0, /*tp_getattr*/
  0, /*tp_setattr*/
  0, /*tp_as_async*/
  0, /*tp_repr*/
  0, /*tp_as_number*/
  0, /*tp_as_sequence*/
  0, /*tp_as_mapping*/
  0, /*tp_hash*/
  0, /*tp_call*/
  0, /*tp_str*/
  0, /*tp_getattro*/
  0, /*tp_setattro*/
  0, /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_VERSION_TAG|Py_TPFLAGS_CHECKTYPES|Py_TPFLAGS_HAVE_NEWBUFFER|Py_TPFLAGS_HAVE_FINALIZE, /*tp_flags*/
  0, /*tp_doc*/
  0, /*tp_traverse*/
  0, /*tp_clear*/
  0, /*tp_richcompare*/
  0, /*tp_weaklistoffset*/
  0, /*tp_iter*/
  0, /*tp_iternext*/
  0, /*tp_methods*/
  0, /*tp_members*/
  0, /*tp_getset*/
  0, /*tp_base*/
  0, /*tp_dict*/
  0, /*tp_descr_get*/
  0, /*tp_descr_set*/
  #if !CYTHON_USE_TYPE_SPECS
  0, /*tp_dictoffset*/
  #endif
  0, /*tp_init*/
  0, /*tp_alloc*/
  __pyx_tp_new_8solver_c___pyx_scope_struct__solve_c, /*tp_new*/
  0, /*tp_free*/
  0, /*tp_is_gc*/
  0, /*tp_bases*/
  0, /*tp_mro*/
  0, /*tp_cache*/
  0, /*tp_subclasses*/
  0, /*tp_weaklist*/
  0, /*tp_del*/
  0, /*tp_version_tag*/
  #if CYTHON_USE_TP_FINALIZE
  0, /*tp_finalize*/
  #else
  NULL, /*tp_finalize*/
  #endif
  #if PY_VERSION_HEX >= 0x030800b1 && (!CYTHON_COMPILING_IN_PYPY || PYPY_VERSION_NUM >= 0x07030800)
  0, /*tp_vectorcall*/
  #endif
  #if __PYX_NEED_TP_PRINT_SLOT == 1
  0, /*tp_print*/
  #endif
  #if PY_VERSION_HEX >= 0x030C0000
  0, /*tp_watched*/
  #endif
  #if PY_VERSION_HEX >= 0x030d00A4
  0, /*tp_versions_used*/
  #endif
  #if CYTHON_COMPILING_IN_PYPY && PY_VERSION_HEX >= 0x03090000 && PY_VERSION_HEX < 0x030a0000
  0, /*tp_pypy_flags*/
  #endif
};
#endif

static PyMethodDef __pyx_methods[] = {
  {0, 0, 0, 0}
};
/* #### Code section: initfunc_declarations ### */
static CYTHON_SMALL_CODE int __Pyx_InitCachedBuiltins(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_InitCachedConstants(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_InitGlobals(void); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_InitConstants(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_global_init_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_variable_export_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_function_export_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_type_init_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_type_import_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_variable_import_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_modinit_function_import_code(__pyx_mstatetype *__pyx_mstate); /*proto*/
static CYTHON_SMALL_CODE int __Pyx_CreateCodeObjects(__pyx_mstatetype *__pyx_mstate); /*proto*/
/* #### Code section: init_module ### */

static int __Pyx_modinit_global_init_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_global_init_code", 0);
  /*--- Global init code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

static int __Pyx_modinit_variable_export_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_variable_export_code", 0);
  /*--- Variable export code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

static int __Pyx_modinit_function_export_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_function_export_code", 0);
  /*--- Function export code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

static int __Pyx_modinit_type_init_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  __Pyx_RefNannySetupContext("__Pyx_modinit_type_init_code", 0);
  /*--- Type init code ---*/
  #if CYTHON_USE_TYPE_SPECS
  __pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c = (PyTypeObject *) __Pyx_PyType_FromModuleAndSpec(__pyx_m, &__pyx_type_8solver_c___pyx_scope_struct__solve_c_spec, NULL); if (unlikely(!__pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c)) __PYX_ERR(0, 66, __pyx_L1_error)
  if (__Pyx_fix_up_extension_type_from_spec(&__pyx_type_8solver_c___pyx_scope_struct__solve_c_spec, __pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c) < 0) __PYX_ERR(0, 66, __pyx_L1_error)
  #else
  __pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c = &__pyx_type_8solver_c___pyx_scope_struct__solve_c;
  #endif
  #if !CYTHON_COMPILING_IN_LIMITED_API
  #endif
  #if !CYTHON_USE_TYPE_SPECS
  if (__Pyx_PyType_Ready(__pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c) < 0) __PYX_ERR(0, 66, __pyx_L1_error)
  #endif
  #if !CYTHON_COMPILING_IN_LIMITED_API
  if ((CYTHON_USE_TYPE_SLOTS && CYTHON_USE_PYTYPE_LOOKUP) && likely(!__pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c->tp_dictoffset && __pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c->tp_getattro == PyObject_GenericGetAttr)) {
    __pyx_mstate->__pyx_ptype_8solver_c___pyx_scope_struct__solve_c->tp_getattro = PyObject_GenericGetAttr;
  }
  #endif
  __Pyx_RefNannyFinishContext();
  return 0;
  __pyx_L1_error:;
  __Pyx_RefNannyFinishContext();
  return -1;
}

static int __Pyx_modinit_type_import_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_type_import_code", 0);
  /*--- Type import code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

static int __Pyx_modinit_variable_import_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_variable_import_code", 0);
  /*--- Variable import code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

static int __Pyx_modinit_function_import_code(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_modinit_function_import_code", 0);
  /*--- Function import code ---*/
  __Pyx_RefNannyFinishContext();
  return 0;
}

#if CYTHON_PEP489_MULTI_PHASE_INIT
static PyObject* __pyx_pymod_create(PyObject *spec, PyModuleDef *def); /*proto*/
static int __pyx_pymod_exec_solver_c(PyObject* module); /*proto*/
static PyModuleDef_Slot __pyx_moduledef_slots[] = {
  {Py_mod_create, (void*)__pyx_pymod_create},
  {Py_mod_exec, (void*)__pyx_pymod_exec_solver_c},
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
  {Py_mod_gil, Py_MOD_GIL_USED},
  #endif
  #if PY_VERSION_HEX >= 0x030C0000 && CYTHON_USE_MODULE_STATE
  {Py_mod_multiple_interpreters, Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED},
  #endif
  {0, NULL}
};
#endif

#ifdef __cplusplus
namespace {
  struct PyModuleDef __pyx_moduledef =
  #else
  static struct PyModuleDef __pyx_moduledef =
  #endif
  {
      PyModuleDef_HEAD_INIT,
      "solver_c",
      0, /* m_doc */
    #if CYTHON_USE_MODULE_STATE
      sizeof(__pyx_mstatetype), /* m_size */
    #else
      (CYTHON_PEP489_MULTI_PHASE_INIT) ? 0 : -1, /* m_size */
    #endif
      __pyx_methods /* m_methods */,
    #if CYTHON_PEP489_MULTI_PHASE_INIT
      __pyx_moduledef_slots, /* m_slots */
    #else
      NULL, /* m_reload */
    #endif
    #if CYTHON_USE_MODULE_STATE
      __pyx_m_traverse, /* m_traverse */
      __pyx_m_clear, /* m_clear */
      NULL /* m_free */
    #else
      NULL, /* m_traverse */
      NULL, /* m_clear */
      NULL /* m_free */
    #endif
  };
  #ifdef __cplusplus
} /* anonymous namespace */
#endif

/* PyModInitFuncType */
#ifndef CYTHON_NO_PYINIT_EXPORT
  #define __Pyx_PyMODINIT_FUNC PyMODINIT_FUNC
#else
  #ifdef __cplusplus
  #define __Pyx_PyMODINIT_FUNC extern "C" PyObject *
  #else
  #define __Pyx_PyMODINIT_FUNC PyObject *
  #endif
#endif

__Pyx_PyMODINIT_FUNC PyInit_solver_c(void) CYTHON_SMALL_CODE; /*proto*/
__Pyx_PyMODINIT_FUNC PyInit_solver_c(void)
#if CYTHON_PEP489_MULTI_PHASE_INIT
{
  return PyModuleDef_Init(&__pyx_moduledef);
}
/* ModuleCreationPEP489 */
#if CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX < 0x03090000
static PY_INT64_T __Pyx_GetCurrentInterpreterId(void) {
    {
        PyObject *module = PyImport_ImportModule("_interpreters"); // 3.13+ I think
        if (!module) {
            PyErr_Clear(); // just try the 3.8-3.12 version
            module = PyImport_ImportModule("_xxsubinterpreters");
            if (!module) goto bad;
        }
        PyObject *current = PyObject_CallMethod(module, "get_current", NULL);
        Py_DECREF(module);
        if (!current) goto bad;
        if (PyTuple_Check(current)) {
            PyObject *new_current = PySequence_GetItem(current, 0);
            Py_DECREF(current);
            current = new_current;
            if (!new_current) goto bad;
        }
        long long as_c_int = PyLong_AsLongLong(current);
        Py_DECREF(current);
        return as_c_int;
    }
  bad:
    PySys_WriteStderr("__Pyx_GetCurrentInterpreterId failed. Try setting the C define CYTHON_PEP489_MULTI_PHASE_INIT=0\n");
    return -1;
}
#endif
#if !CYTHON_USE_MODULE_STATE
static CYTHON_SMALL_CODE int __Pyx_check_single_interpreter(void) {
    static PY_INT64_T main_interpreter_id = -1;
#if CYTHON_COMPILING_IN_GRAAL
    PY_INT64_T current_id = PyInterpreterState_GetIDFromThreadState(PyThreadState_Get());
#elif CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX >= 0x03090000
    PY_INT64_T current_id = PyInterpreterState_GetID(PyInterpreterState_Get());
#elif CYTHON_COMPILING_IN_LIMITED_API
    PY_INT64_T current_id = __Pyx_GetCurrentInterpreterId();
#else
    PY_INT64_T current_id = PyInterpreterState_GetID(PyThreadState_Get()->interp);
#endif
    if (unlikely(current_id == -1)) {
        return -1;
    }
    if (main_interpreter_id == -1) {
        main_interpreter_id = current_id;
        return 0;
    } else if (unlikely(main_interpreter_id != current_id)) {
        PyErr_SetString(
            PyExc_ImportError,
            "Interpreter change detected - this module can only be loaded into one interpreter per process.");
        return -1;
    }
    return 0;
}
#endif
static CYTHON_SMALL_CODE int __Pyx_copy_spec_to_module(PyObject *spec, PyObject *moddict, const char* from_name, const char* to_name, int allow_none)
{
    PyObject *value = PyObject_GetAttrString(spec, from_name);
    int result = 0;
    if (likely(value)) {
        if (allow_none || value != Py_None) {
            result = PyDict_SetItemString(moddict, to_name, value);
        }
        Py_DECREF(value);
    } else if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
        PyErr_Clear();
    } else {
        result = -1;
    }
    return result;
}
static CYTHON_SMALL_CODE PyObject* __pyx_pymod_create(PyObject *spec, PyModuleDef *def) {
    PyObject *module = NULL, *moddict, *modname;
    CYTHON_UNUSED_VAR(def);
    #if !CYTHON_USE_MODULE_STATE
    if (__Pyx_check_single_interpreter())
        return NULL;
    #endif
    if (__pyx_m)
        return __Pyx_NewRef(__pyx_m);
    modname = PyObject_GetAttrString(spec, "name");
    if (unlikely(!modname)) goto bad;
    module = PyModule_NewObject(modname);
    Py_DECREF(modname);
    if (unlikely(!module)) goto bad;
    moddict = PyModule_GetDict(module);
    if (unlikely(!moddict)) goto bad;
    if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "loader", "__loader__", 1) < 0)) goto bad;
    if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "origin", "__file__", 1) < 0)) goto bad;
    if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "parent", "__package__", 1) < 0)) goto bad;
    if (unlikely(__Pyx_copy_spec_to_module(spec, moddict, "submodule_search_locations", "__path__", 0) < 0)) goto bad;
    return module;
bad:
    Py_XDECREF(module);
    return NULL;
}


static CYTHON_SMALL_CODE int __pyx_pymod_exec_solver_c(PyObject *__pyx_pyinit_module)
#endif
{
  int stringtab_initialized = 0;
  #if CYTHON_USE_MODULE_STATE
  int pystate_addmodule_run = 0;
  #endif
  __pyx_mstatetype *__pyx_mstate = NULL;
  PyObject *__pyx_t_1 = NULL;
  PyObject *__pyx_t_2 = NULL;
  int __pyx_lineno = 0;
  const char *__pyx_filename = NULL;
  int __pyx_clineno = 0;
  __Pyx_RefNannyDeclarations
  #if CYTHON_PEP489_MULTI_PHASE_INIT
  if (__pyx_m) {
    if (__pyx_m == __pyx_pyinit_module) return 0;
    PyErr_SetString(PyExc_RuntimeError, "Module 'solver_c' has already been imported. Re-initialisation is not supported.");
    return -1;
  }
  #else
  if (__pyx_m) return __Pyx_NewRef(__pyx_m);
  #endif
  /*--- Module creation code ---*/
  #if CYTHON_PEP489_MULTI_PHASE_INIT
  __pyx_t_1 = __pyx_pyinit_module;
  Py_INCREF(__pyx_t_1);
  #else
  __pyx_t_1 = PyModule_Create(&__pyx_moduledef); if (unlikely(!__pyx_t_1)) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #if CYTHON_USE_MODULE_STATE
  {
    int add_module_result = __Pyx_State_AddModule(__pyx_t_1, &__pyx_moduledef);
    __pyx_t_1 = 0; /* transfer ownership from __pyx_t_1 to "solver_c" pseudovariable */
    if (unlikely((add_module_result < 0))) __PYX_ERR(0, 1, __pyx_L1_error)
    pystate_addmodule_run = 1;
  }
  #else
  __pyx_m = __pyx_t_1;
  #endif
  #if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
  PyUnstable_Module_SetGIL(__pyx_m, Py_MOD_GIL_USED);
  #endif
  __pyx_mstate = __pyx_mstate_global;
  CYTHON_UNUSED_VAR(__pyx_t_1);
  __pyx_mstate->__pyx_d = PyModule_GetDict(__pyx_m); if (unlikely(!__pyx_mstate->__pyx_d)) __PYX_ERR(0, 1, __pyx_L1_error)
  Py_INCREF(__pyx_mstate->__pyx_d);
  __pyx_mstate->__pyx_b = __Pyx_PyImport_AddModuleRef(__Pyx_BUILTIN_MODULE_NAME); if (unlikely(!__pyx_mstate->__pyx_b)) __PYX_ERR(0, 1, __pyx_L1_error)
  __pyx_mstate->__pyx_cython_runtime = __Pyx_PyImport_AddModuleRef("cython_runtime"); if (unlikely(!__pyx_mstate->__pyx_cython_runtime)) __PYX_ERR(0, 1, __pyx_L1_error)
  if (PyObject_SetAttrString(__pyx_m, "__builtins__", __pyx_mstate->__pyx_b) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  /* ImportRefnannyAPI */
  #if CYTHON_REFNANNY
__Pyx_RefNanny = __Pyx_RefNannyImportAPI("refnanny");
if (!__Pyx_RefNanny) {
  PyErr_Clear();
  __Pyx_RefNanny = __Pyx_RefNannyImportAPI("Cython.Runtime.refnanny");
  if (!__Pyx_RefNanny)
      Py_FatalError("failed to import 'refnanny' module");
}
#endif

__Pyx_RefNannySetupContext("PyInit_solver_c", 0);
  if (__Pyx_check_binary_version(__PYX_LIMITED_VERSION_HEX, __Pyx_get_runtime_version(), CYTHON_COMPILING_IN_LIMITED_API) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #ifdef __Pxy_PyFrame_Initialize_Offsets
  __Pxy_PyFrame_Initialize_Offsets();
  #endif
  __pyx_mstate->__pyx_empty_tuple = PyTuple_New(0); if (unlikely(!__pyx_mstate->__pyx_empty_tuple)) __PYX_ERR(0, 1, __pyx_L1_error)
  __pyx_mstate->__pyx_empty_bytes = PyBytes_FromStringAndSize("", 0); if (unlikely(!__pyx_mstate->__pyx_empty_bytes)) __PYX_ERR(0, 1, __pyx_L1_error)
  __pyx_mstate->__pyx_empty_unicode = PyUnicode_FromStringAndSize("", 0); if (unlikely(!__pyx_mstate->__pyx_empty_unicode)) __PYX_ERR(0, 1, __pyx_L1_error)
  /*--- Initialize various global constants etc. ---*/
  if (__Pyx_InitConstants(__pyx_mstate) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  stringtab_initialized = 1;
  if (__Pyx_InitGlobals() < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #if 0 || defined(__Pyx_CyFunction_USED) || defined(__Pyx_FusedFunction_USED) || defined(__Pyx_Coroutine_USED) || defined(__Pyx_Generator_USED) || defined(__Pyx_AsyncGen_USED)
  if (__pyx_CommonTypesMetaclass_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #ifdef __Pyx_CyFunction_USED
  if (__pyx_CyFunction_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #ifdef __Pyx_FusedFunction_USED
  if (__pyx_FusedFunction_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #ifdef __Pyx_Coroutine_USED
  if (__pyx_Coroutine_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #ifdef __Pyx_Generator_USED
  if (__pyx_Generator_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  #ifdef __Pyx_AsyncGen_USED
  if (__pyx_AsyncGen_init(__pyx_m) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  #endif
  /*--- Library function declarations ---*/
  if (__pyx_module_is_main_solver_c) {
    if (PyObject_SetAttr(__pyx_m, __pyx_mstate_global->__pyx_n_u_name, __pyx_mstate_global->__pyx_n_u_main) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  }
  {
    PyObject *modules = PyImport_GetModuleDict(); if (unlikely(!modules)) __PYX_ERR(0, 1, __pyx_L1_error)
    if (!PyDict_GetItemString(modules, "solver_c")) {
      if (unlikely((PyDict_SetItemString(modules, "solver_c", __pyx_m) < 0))) __PYX_ERR(0, 1, __pyx_L1_error)
    }
  }
  /*--- Builtin init code ---*/
  if (__Pyx_InitCachedBuiltins(__pyx_mstate) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  /*--- Constants init code ---*/
  if (__Pyx_InitCachedConstants(__pyx_mstate) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  if (__Pyx_CreateCodeObjects(__pyx_mstate) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  /*--- Global type/function init code ---*/
  (void)__Pyx_modinit_global_init_code(__pyx_mstate);
  (void)__Pyx_modinit_variable_export_code(__pyx_mstate);
  (void)__Pyx_modinit_function_export_code(__pyx_mstate);
  if (unlikely((__Pyx_modinit_type_init_code(__pyx_mstate) < 0))) __PYX_ERR(0, 1, __pyx_L1_error)
  (void)__Pyx_modinit_type_import_code(__pyx_mstate);
  (void)__Pyx_modinit_variable_import_code(__pyx_mstate);
  (void)__Pyx_modinit_function_import_code(__pyx_mstate);
  /*--- Execution code ---*/

  /* "solver_c.pyx":66
 *         X |= v
 * 
 * def solve_c(object problem):             # <<<<<<<<<<<<<<
 *     cdef Py_ssize_t n = len(problem)
 *     cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
*/
  __pyx_t_2 = __Pyx_CyFunction_New(&__pyx_mdef_8solver_c_1solve_c, 0, __pyx_mstate_global->__pyx_n_u_solve_c, NULL, __pyx_mstate_global->__pyx_n_u_solver_c, __pyx_mstate_global->__pyx_d, ((PyObject *)__pyx_mstate_global->__pyx_codeobj_tab[1])); if (unlikely(!__pyx_t_2)) __PYX_ERR(0, 66, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_2);
  if (PyDict_SetItem(__pyx_mstate_global->__pyx_d, __pyx_mstate_global->__pyx_n_u_solve_c, __pyx_t_2) < 0) __PYX_ERR(0, 66, __pyx_L1_error)
  __Pyx_DECREF(__pyx_t_2); __pyx_t_2 = 0;

  /* "solver_c.pyx":1
 * # cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False             # <<<<<<<<<<<<<<
 * cimport cython
 * from cpython.mem cimport PyMem_Malloc, PyMem_Free
*/
  __pyx_t_2 = __Pyx_PyDict_NewPresized(0); if (unlikely(!__pyx_t_2)) __PYX_ERR(0, 1, __pyx_L1_error)
  __Pyx_GOTREF(__pyx_t_2);
  if (PyDict_SetItem(__pyx_mstate_global->__pyx_d, __pyx_mstate_global->__pyx_n_u_test, __pyx_t_2) < 0) __PYX_ERR(0, 1, __pyx_L1_error)
  __Pyx_DECREF(__pyx_t_2); __pyx_t_2 = 0;

  /*--- Wrapped vars code ---*/

  goto __pyx_L0;
  __pyx_L1_error:;
  __Pyx_XDECREF(__pyx_t_2);
  if (__pyx_m) {
    if (__pyx_mstate->__pyx_d && stringtab_initialized) {
      __Pyx_AddTraceback("init solver_c", __pyx_clineno, __pyx_lineno, __pyx_filename);
    }
    #if !CYTHON_USE_MODULE_STATE
    Py_CLEAR(__pyx_m);
    #else
    Py_DECREF(__pyx_m);
    if (pystate_addmodule_run) {
      PyObject *tp, *value, *tb;
      PyErr_Fetch(&tp, &value, &tb);
      PyState_RemoveModule(&__pyx_moduledef);
      PyErr_Restore(tp, value, tb);
    }
    #endif
  } else if (!PyErr_Occurred()) {
    PyErr_SetString(PyExc_ImportError, "init solver_c");
  }
  __pyx_L0:;
  __Pyx_RefNannyFinishContext();
  #if CYTHON_PEP489_MULTI_PHASE_INIT
  return (__pyx_m != NULL) ? 0 : -1;
  #else
  return __pyx_m;
  #endif
}
/* #### Code section: pystring_table ### */

typedef struct {
    const char *s;
#if 25 <= 65535
    const unsigned short n;
#elif 25 / 2 < INT_MAX
    const unsigned int n;
#elif 25 / 2 < LONG_MAX
    const unsigned long n;
#else
    const Py_ssize_t n;
#endif
#if 1 <= 31
    const unsigned int encoding : 5;
#elif 1 <= 255
    const unsigned char encoding;
#elif 1 <= 65535
    const unsigned short encoding;
#else
    const Py_ssize_t encoding;
#endif
    const unsigned int is_unicode : 1;
    const unsigned int intern : 1;
} __Pyx_StringTabEntry;
static const char * const __pyx_string_tab_encodings[] = { 0 };
static const __Pyx_StringTabEntry __pyx_string_tab[] = {
  {__pyx_k_, sizeof(__pyx_k_), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_ */
  {__pyx_k_R0, sizeof(__pyx_k_R0), 0, 1, 1}, /* PyObject cname: __pyx_n_u_R0 */
  {__pyx_k_asyncio_coroutines, sizeof(__pyx_k_asyncio_coroutines), 0, 1, 1}, /* PyObject cname: __pyx_n_u_asyncio_coroutines */
  {__pyx_k_bestR, sizeof(__pyx_k_bestR), 0, 1, 1}, /* PyObject cname: __pyx_n_u_bestR */
  {__pyx_k_bestR_p, sizeof(__pyx_k_bestR_p), 0, 1, 1}, /* PyObject cname: __pyx_n_u_bestR_p */
  {__pyx_k_best_size, sizeof(__pyx_k_best_size), 0, 1, 1}, /* PyObject cname: __pyx_n_u_best_size */
  {__pyx_k_best_size_p, sizeof(__pyx_k_best_size_p), 0, 1, 1}, /* PyObject cname: __pyx_n_u_best_size_p */
  {__pyx_k_bit_count, sizeof(__pyx_k_bit_count), 0, 1, 1}, /* PyObject cname: __pyx_n_u_bit_count */
  {__pyx_k_cline_in_traceback, sizeof(__pyx_k_cline_in_traceback), 0, 1, 1}, /* PyObject cname: __pyx_n_u_cline_in_traceback */
  {__pyx_k_disable, sizeof(__pyx_k_disable), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_disable */
  {__pyx_k_enable, sizeof(__pyx_k_enable), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_enable */
  {__pyx_k_full, sizeof(__pyx_k_full), 0, 1, 1}, /* PyObject cname: __pyx_n_u_full */
  {__pyx_k_func, sizeof(__pyx_k_func), 0, 1, 1}, /* PyObject cname: __pyx_n_u_func */
  {__pyx_k_gc, sizeof(__pyx_k_gc), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_gc */
  {__pyx_k_i, sizeof(__pyx_k_i), 0, 1, 1}, /* PyObject cname: __pyx_n_u_i */
  {__pyx_k_is_coroutine, sizeof(__pyx_k_is_coroutine), 0, 1, 1}, /* PyObject cname: __pyx_n_u_is_coroutine */
  {__pyx_k_isenabled, sizeof(__pyx_k_isenabled), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_isenabled */
  {__pyx_k_j, sizeof(__pyx_k_j), 0, 1, 1}, /* PyObject cname: __pyx_n_u_j */
  {__pyx_k_key, sizeof(__pyx_k_key), 0, 1, 1}, /* PyObject cname: __pyx_n_u_key */
  {__pyx_k_lambda, sizeof(__pyx_k_lambda), 0, 1, 1}, /* PyObject cname: __pyx_n_u_lambda */
  {__pyx_k_main, sizeof(__pyx_k_main), 0, 1, 1}, /* PyObject cname: __pyx_n_u_main */
  {__pyx_k_mask, sizeof(__pyx_k_mask), 0, 1, 1}, /* PyObject cname: __pyx_n_u_mask */
  {__pyx_k_module, sizeof(__pyx_k_module), 0, 1, 1}, /* PyObject cname: __pyx_n_u_module */
  {__pyx_k_n, sizeof(__pyx_k_n), 0, 1, 1}, /* PyObject cname: __pyx_n_u_n */
  {__pyx_k_name, sizeof(__pyx_k_name), 0, 1, 1}, /* PyObject cname: __pyx_n_u_name */
  {__pyx_k_neighbors, sizeof(__pyx_k_neighbors), 0, 1, 1}, /* PyObject cname: __pyx_n_u_neighbors */
  {__pyx_k_order, sizeof(__pyx_k_order), 0, 1, 1}, /* PyObject cname: __pyx_n_u_order */
  {__pyx_k_pop, sizeof(__pyx_k_pop), 0, 1, 1}, /* PyObject cname: __pyx_n_u_pop */
  {__pyx_k_problem, sizeof(__pyx_k_problem), 0, 1, 1}, /* PyObject cname: __pyx_n_u_problem */
  {__pyx_k_qualname, sizeof(__pyx_k_qualname), 0, 1, 1}, /* PyObject cname: __pyx_n_u_qualname */
  {__pyx_k_range, sizeof(__pyx_k_range), 0, 1, 1}, /* PyObject cname: __pyx_n_u_range */
  {__pyx_k_res, sizeof(__pyx_k_res), 0, 1, 1}, /* PyObject cname: __pyx_n_u_res */
  {__pyx_k_set_name, sizeof(__pyx_k_set_name), 0, 1, 1}, /* PyObject cname: __pyx_n_u_set_name */
  {__pyx_k_solve_c, sizeof(__pyx_k_solve_c), 0, 1, 1}, /* PyObject cname: __pyx_n_u_solve_c */
  {__pyx_k_solve_c_locals_lambda, sizeof(__pyx_k_solve_c_locals_lambda), 0, 1, 1}, /* PyObject cname: __pyx_n_u_solve_c_locals_lambda */
  {__pyx_k_solver_c, sizeof(__pyx_k_solver_c), 0, 1, 1}, /* PyObject cname: __pyx_n_u_solver_c */
  {__pyx_k_solver_c_pyx, sizeof(__pyx_k_solver_c_pyx), 0, 1, 0}, /* PyObject cname: __pyx_kp_u_solver_c_pyx */
  {__pyx_k_sort, sizeof(__pyx_k_sort), 0, 1, 1}, /* PyObject cname: __pyx_n_u_sort */
  {__pyx_k_test, sizeof(__pyx_k_test), 0, 1, 1}, /* PyObject cname: __pyx_n_u_test */
  {__pyx_k_x, sizeof(__pyx_k_x), 0, 1, 1}, /* PyObject cname: __pyx_n_u_x */
  {0, 0, 0, 0, 0}
};
/* InitStrings.proto */
static int __Pyx_InitStrings(__Pyx_StringTabEntry const *t, PyObject **target, const char* const* encoding_names);

/* #### Code section: cached_builtins ### */

static int __Pyx_InitCachedBuiltins(__pyx_mstatetype *__pyx_mstate) {
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __pyx_builtin_range = __Pyx_GetBuiltinName(__pyx_mstate->__pyx_n_u_range); if (!__pyx_builtin_range) __PYX_ERR(0, 77, __pyx_L1_error)
  return 0;
  __pyx_L1_error:;
  return -1;
}
/* #### Code section: cached_constants ### */

static int __Pyx_InitCachedConstants(__pyx_mstatetype *__pyx_mstate) {
  __Pyx_RefNannyDeclarations
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __Pyx_RefNannySetupContext("__Pyx_InitCachedConstants", 0);
  __Pyx_RefNannyFinishContext();
  return 0;
}
/* #### Code section: init_constants ### */

static int __Pyx_InitConstants(__pyx_mstatetype *__pyx_mstate) {
  CYTHON_UNUSED_VAR(__pyx_mstate);
  __pyx_mstate->__pyx_umethod_PyDict_Type_pop.type = (PyObject*)&PyDict_Type;
  __pyx_mstate->__pyx_umethod_PyDict_Type_pop.method_name = &__pyx_mstate->__pyx_n_u_pop;
  if (__Pyx_InitStrings(__pyx_string_tab, __pyx_mstate->__pyx_string_tab, __pyx_string_tab_encodings) < 0) __PYX_ERR(0, 1, __pyx_L1_error);
  return 0;
  __pyx_L1_error:;
  return -1;
}
/* #### Code section: init_codeobjects ### */
\
        typedef struct {
            unsigned int argcount : 1;
            unsigned int num_posonly_args : 1;
            unsigned int num_kwonly_args : 1;
            unsigned int nlocals : 4;
            unsigned int flags : 10;
            unsigned int first_line : 7;
            unsigned int line_table_length : 13;
        } __Pyx_PyCode_New_function_description;
/* NewCodeObj.proto */
static PyObject* __Pyx_PyCode_New(
        const __Pyx_PyCode_New_function_description descr,
        PyObject * const *varnames,
        PyObject *filename,
        PyObject *funcname,
        const char *line_table,
        PyObject *tuple_dedup_map
);


static int __Pyx_CreateCodeObjects(__pyx_mstatetype *__pyx_mstate) {
  PyObject* tuple_dedup_map = PyDict_New();
  if (unlikely(!tuple_dedup_map)) return -1;
  {
    const __Pyx_PyCode_New_function_description descr = {1, 0, 0, 1, (unsigned int)(CO_OPTIMIZED|CO_NEWLOCALS), 86, 12};
    PyObject* const varnames[] = {__pyx_mstate->__pyx_n_u_x};
    __pyx_mstate_global->__pyx_codeobj_tab[0] = __Pyx_PyCode_New(descr, varnames, __pyx_mstate->__pyx_kp_u_solver_c_pyx, __pyx_mstate->__pyx_n_u_lambda, __pyx_k_iq_Q, tuple_dedup_map); if (unlikely(!__pyx_mstate_global->__pyx_codeobj_tab[0])) goto bad;
  }
  {
    const __Pyx_PyCode_New_function_description descr = {1, 0, 0, 14, (unsigned int)(CO_OPTIMIZED|CO_NEWLOCALS), 66, 290};
    PyObject* const varnames[] = {__pyx_mstate->__pyx_n_u_problem, __pyx_mstate->__pyx_n_u_n, __pyx_mstate->__pyx_n_u_neighbors, __pyx_mstate->__pyx_n_u_i, __pyx_mstate->__pyx_n_u_j, __pyx_mstate->__pyx_n_u_mask, __pyx_mstate->__pyx_n_u_full, __pyx_mstate->__pyx_n_u_best_size, __pyx_mstate->__pyx_n_u_bestR, __pyx_mstate->__pyx_n_u_best_size_p, __pyx_mstate->__pyx_n_u_bestR_p, __pyx_mstate->__pyx_n_u_order, __pyx_mstate->__pyx_n_u_R0, __pyx_mstate->__pyx_n_u_res};
    __pyx_mstate_global->__pyx_codeobj_tab[1] = __Pyx_PyCode_New(descr, varnames, __pyx_mstate->__pyx_kp_u_solver_c_pyx, __pyx_mstate->__pyx_n_u_solve_c, __pyx_k_1A_Qb_AQ_E_3c_1_U_1_uBb_Rs_E_aq, tuple_dedup_map); if (unlikely(!__pyx_mstate_global->__pyx_codeobj_tab[1])) goto bad;
  }
  Py_DECREF(tuple_dedup_map);
  return 0;
  bad:
  Py_DECREF(tuple_dedup_map);
  return -1;
}
/* #### Code section: init_globals ### */

static int __Pyx_InitGlobals(void) {
  /* PythonCompatibility.init */
  if (likely(__Pyx_init_co_variables() == 0)); else

if (unlikely(PyErr_Occurred())) __PYX_ERR(0, 1, __pyx_L1_error)

  /* CachedMethodType.init */
  #if CYTHON_COMPILING_IN_LIMITED_API
{
    PyObject *typesModule=NULL;
    typesModule = PyImport_ImportModule("types");
    if (typesModule) {
        __pyx_mstate_global->__Pyx_CachedMethodType = PyObject_GetAttrString(typesModule, "MethodType");
        Py_DECREF(typesModule);
    }
} // error handling follows
#endif

if (unlikely(PyErr_Occurred())) __PYX_ERR(0, 1, __pyx_L1_error)

  return 0;
  __pyx_L1_error:;
  return -1;
}
/* #### Code section: cleanup_globals ### */
/* #### Code section: cleanup_module ### */
/* #### Code section: main_method ### */
/* #### Code section: utility_code_pragmas ### */
#ifdef _MSC_VER
#pragma warning( push )
/* Warning 4127: conditional expression is constant
 * Cython uses constant conditional expressions to allow in inline functions to be optimized at
 * compile-time, so this warning is not useful
 */
#pragma warning( disable : 4127 )
#endif



/* #### Code section: utility_code_def ### */

/* --- Runtime support code --- */
/* Refnanny */
#if CYTHON_REFNANNY
static __Pyx_RefNannyAPIStruct *__Pyx_RefNannyImportAPI(const char *modname) {
    PyObject *m = NULL, *p = NULL;
    void *r = NULL;
    m = PyImport_ImportModule(modname);
    if (!m) goto end;
    p = PyObject_GetAttrString(m, "RefNannyAPI");
    if (!p) goto end;
    r = PyLong_AsVoidPtr(p);
end:
    Py_XDECREF(p);
    Py_XDECREF(m);
    return (__Pyx_RefNannyAPIStruct *)r;
}
#endif

/* PyErrExceptionMatches */
#if CYTHON_FAST_THREAD_STATE
static int __Pyx_PyErr_ExceptionMatchesTuple(PyObject *exc_type, PyObject *tuple) {
    Py_ssize_t i, n;
    n = PyTuple_GET_SIZE(tuple);
    for (i=0; i<n; i++) {
        if (exc_type == PyTuple_GET_ITEM(tuple, i)) return 1;
    }
    for (i=0; i<n; i++) {
        if (__Pyx_PyErr_GivenExceptionMatches(exc_type, PyTuple_GET_ITEM(tuple, i))) return 1;
    }
    return 0;
}
static CYTHON_INLINE int __Pyx_PyErr_ExceptionMatchesInState(PyThreadState* tstate, PyObject* err) {
    int result;
    PyObject *exc_type;
#if PY_VERSION_HEX >= 0x030C00A6
    PyObject *current_exception = tstate->current_exception;
    if (unlikely(!current_exception)) return 0;
    exc_type = (PyObject*) Py_TYPE(current_exception);
    if (exc_type == err) return 1;
#else
    exc_type = tstate->curexc_type;
    if (exc_type == err) return 1;
    if (unlikely(!exc_type)) return 0;
#endif
    #if CYTHON_AVOID_BORROWED_REFS
    Py_INCREF(exc_type);
    #endif
    if (unlikely(PyTuple_Check(err))) {
        result = __Pyx_PyErr_ExceptionMatchesTuple(exc_type, err);
    } else {
        result = __Pyx_PyErr_GivenExceptionMatches(exc_type, err);
    }
    #if CYTHON_AVOID_BORROWED_REFS
    Py_DECREF(exc_type);
    #endif
    return result;
}
#endif

/* PyErrFetchRestore */
#if CYTHON_FAST_THREAD_STATE
static CYTHON_INLINE void __Pyx_ErrRestoreInState(PyThreadState *tstate, PyObject *type, PyObject *value, PyObject *tb) {
#if PY_VERSION_HEX >= 0x030C00A6
    PyObject *tmp_value;
    assert(type == NULL || (value != NULL && type == (PyObject*) Py_TYPE(value)));
    if (value) {
        #if CYTHON_COMPILING_IN_CPYTHON
        if (unlikely(((PyBaseExceptionObject*) value)->traceback != tb))
        #endif
            PyException_SetTraceback(value, tb);
    }
    tmp_value = tstate->current_exception;
    tstate->current_exception = value;
    Py_XDECREF(tmp_value);
    Py_XDECREF(type);
    Py_XDECREF(tb);
#else
    PyObject *tmp_type, *tmp_value, *tmp_tb;
    tmp_type = tstate->curexc_type;
    tmp_value = tstate->curexc_value;
    tmp_tb = tstate->curexc_traceback;
    tstate->curexc_type = type;
    tstate->curexc_value = value;
    tstate->curexc_traceback = tb;
    Py_XDECREF(tmp_type);
    Py_XDECREF(tmp_value);
    Py_XDECREF(tmp_tb);
#endif
}
static CYTHON_INLINE void __Pyx_ErrFetchInState(PyThreadState *tstate, PyObject **type, PyObject **value, PyObject **tb) {
#if PY_VERSION_HEX >= 0x030C00A6
    PyObject* exc_value;
    exc_value = tstate->current_exception;
    tstate->current_exception = 0;
    *value = exc_value;
    *type = NULL;
    *tb = NULL;
    if (exc_value) {
        *type = (PyObject*) Py_TYPE(exc_value);
        Py_INCREF(*type);
        #if CYTHON_COMPILING_IN_CPYTHON
        *tb = ((PyBaseExceptionObject*) exc_value)->traceback;
        Py_XINCREF(*tb);
        #else
        *tb = PyException_GetTraceback(exc_value);
        #endif
    }
#else
    *type = tstate->curexc_type;
    *value = tstate->curexc_value;
    *tb = tstate->curexc_traceback;
    tstate->curexc_type = 0;
    tstate->curexc_value = 0;
    tstate->curexc_traceback = 0;
#endif
}
#endif

/* PyObjectGetAttrStr */
#if CYTHON_USE_TYPE_SLOTS
static CYTHON_INLINE PyObject* __Pyx_PyObject_GetAttrStr(PyObject* obj, PyObject* attr_name) {
    PyTypeObject* tp = Py_TYPE(obj);
    if (likely(tp->tp_getattro))
        return tp->tp_getattro(obj, attr_name);
    return PyObject_GetAttr(obj, attr_name);
}
#endif

/* PyObjectGetAttrStrNoError */
#if __PYX_LIMITED_VERSION_HEX < 0x030d0000
static void __Pyx_PyObject_GetAttrStr_ClearAttributeError(void) {
    __Pyx_PyThreadState_declare
    __Pyx_PyThreadState_assign
    if (likely(__Pyx_PyErr_ExceptionMatches(PyExc_AttributeError)))
        __Pyx_PyErr_Clear();
}
#endif
static CYTHON_INLINE PyObject* __Pyx_PyObject_GetAttrStrNoError(PyObject* obj, PyObject* attr_name) {
    PyObject *result;
#if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
    (void) PyObject_GetOptionalAttr(obj, attr_name, &result);
    return result;
#else
#if CYTHON_COMPILING_IN_CPYTHON && CYTHON_USE_TYPE_SLOTS
    PyTypeObject* tp = Py_TYPE(obj);
    if (likely(tp->tp_getattro == PyObject_GenericGetAttr)) {
        return _PyObject_GenericGetAttrWithDict(obj, attr_name, NULL, 1);
    }
#endif
    result = __Pyx_PyObject_GetAttrStr(obj, attr_name);
    if (unlikely(!result)) {
        __Pyx_PyObject_GetAttrStr_ClearAttributeError();
    }
    return result;
#endif
}

/* GetBuiltinName */
static PyObject *__Pyx_GetBuiltinName(PyObject *name) {
    PyObject* result = __Pyx_PyObject_GetAttrStrNoError(__pyx_mstate_global->__pyx_b, name);
    if (unlikely(!result) && !PyErr_Occurred()) {
        PyErr_Format(PyExc_NameError,
            "name '%U' is not defined", name);
    }
    return result;
}

/* ErrOccurredWithGIL */
static CYTHON_INLINE int __Pyx_ErrOccurredWithGIL(void) {
  int err;
  PyGILState_STATE _save = PyGILState_Ensure();
  err = !!PyErr_Occurred();
  PyGILState_Release(_save);
  return err;
}

/* TupleAndListFromArray */
#if !CYTHON_COMPILING_IN_CPYTHON && CYTHON_METH_FASTCALL
static CYTHON_INLINE PyObject *
__Pyx_PyTuple_FromArray(PyObject *const *src, Py_ssize_t n)
{
    PyObject *res;
    Py_ssize_t i;
    if (n <= 0) {
        return __Pyx_NewRef(__pyx_mstate_global->__pyx_empty_tuple);
    }
    res = PyTuple_New(n);
    if (unlikely(res == NULL)) return NULL;
    for (i = 0; i < n; i++) {
        if (unlikely(__Pyx_PyTuple_SET_ITEM(res, i, src[i]) < 0)) {
            Py_DECREF(res);
            return NULL;
        }
        Py_INCREF(src[i]);
    }
    return res;
}
#elif CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE void __Pyx_copy_object_array(PyObject *const *CYTHON_RESTRICT src, PyObject** CYTHON_RESTRICT dest, Py_ssize_t length) {
    PyObject *v;
    Py_ssize_t i;
    for (i = 0; i < length; i++) {
        v = dest[i] = src[i];
        Py_INCREF(v);
    }
}
static CYTHON_INLINE PyObject *
__Pyx_PyTuple_FromArray(PyObject *const *src, Py_ssize_t n)
{
    PyObject *res;
    if (n <= 0) {
        return __Pyx_NewRef(__pyx_mstate_global->__pyx_empty_tuple);
    }
    res = PyTuple_New(n);
    if (unlikely(res == NULL)) return NULL;
    __Pyx_copy_object_array(src, ((PyTupleObject*)res)->ob_item, n);
    return res;
}
static CYTHON_INLINE PyObject *
__Pyx_PyList_FromArray(PyObject *const *src, Py_ssize_t n)
{
    PyObject *res;
    if (n <= 0) {
        return PyList_New(0);
    }
    res = PyList_New(n);
    if (unlikely(res == NULL)) return NULL;
    __Pyx_copy_object_array(src, ((PyListObject*)res)->ob_item, n);
    return res;
}
#endif

/* BytesEquals */
static CYTHON_INLINE int __Pyx_PyBytes_Equals(PyObject* s1, PyObject* s2, int equals) {
#if CYTHON_COMPILING_IN_PYPY || CYTHON_COMPILING_IN_LIMITED_API || CYTHON_COMPILING_IN_GRAAL ||\
        !(CYTHON_ASSUME_SAFE_SIZE && CYTHON_ASSUME_SAFE_MACROS)
    return PyObject_RichCompareBool(s1, s2, equals);
#else
    if (s1 == s2) {
        return (equals == Py_EQ);
    } else if (PyBytes_CheckExact(s1) & PyBytes_CheckExact(s2)) {
        const char *ps1, *ps2;
        Py_ssize_t length = PyBytes_GET_SIZE(s1);
        if (length != PyBytes_GET_SIZE(s2))
            return (equals == Py_NE);
        ps1 = PyBytes_AS_STRING(s1);
        ps2 = PyBytes_AS_STRING(s2);
        if (ps1[0] != ps2[0]) {
            return (equals == Py_NE);
        } else if (length == 1) {
            return (equals == Py_EQ);
        } else {
            int result;
#if CYTHON_USE_UNICODE_INTERNALS && (PY_VERSION_HEX < 0x030B0000)
            Py_hash_t hash1, hash2;
            hash1 = ((PyBytesObject*)s1)->ob_shash;
            hash2 = ((PyBytesObject*)s2)->ob_shash;
            if (hash1 != hash2 && hash1 != -1 && hash2 != -1) {
                return (equals == Py_NE);
            }
#endif
            result = memcmp(ps1, ps2, (size_t)length);
            return (equals == Py_EQ) ? (result == 0) : (result != 0);
        }
    } else if ((s1 == Py_None) & PyBytes_CheckExact(s2)) {
        return (equals == Py_NE);
    } else if ((s2 == Py_None) & PyBytes_CheckExact(s1)) {
        return (equals == Py_NE);
    } else {
        int result;
        PyObject* py_result = PyObject_RichCompare(s1, s2, equals);
        if (!py_result)
            return -1;
        result = __Pyx_PyObject_IsTrue(py_result);
        Py_DECREF(py_result);
        return result;
    }
#endif
}

/* UnicodeEquals */
static CYTHON_INLINE int __Pyx_PyUnicode_Equals(PyObject* s1, PyObject* s2, int equals) {
#if CYTHON_COMPILING_IN_PYPY || CYTHON_COMPILING_IN_LIMITED_API || CYTHON_COMPILING_IN_GRAAL
    return PyObject_RichCompareBool(s1, s2, equals);
#else
    int s1_is_unicode, s2_is_unicode;
    if (s1 == s2) {
        goto return_eq;
    }
    s1_is_unicode = PyUnicode_CheckExact(s1);
    s2_is_unicode = PyUnicode_CheckExact(s2);
    if (s1_is_unicode & s2_is_unicode) {
        Py_ssize_t length, length2;
        int kind;
        void *data1, *data2;
        #if !CYTHON_COMPILING_IN_LIMITED_API
        if (unlikely(__Pyx_PyUnicode_READY(s1) < 0) || unlikely(__Pyx_PyUnicode_READY(s2) < 0))
            return -1;
        #endif
        length = __Pyx_PyUnicode_GET_LENGTH(s1);
        #if !CYTHON_ASSUME_SAFE_SIZE
        if (unlikely(length < 0)) return -1;
        #endif
        length2 = __Pyx_PyUnicode_GET_LENGTH(s2);
        #if !CYTHON_ASSUME_SAFE_SIZE
        if (unlikely(length2 < 0)) return -1;
        #endif
        if (length != length2) {
            goto return_ne;
        }
#if CYTHON_USE_UNICODE_INTERNALS
        {
            Py_hash_t hash1, hash2;
            hash1 = ((PyASCIIObject*)s1)->hash;
            hash2 = ((PyASCIIObject*)s2)->hash;
            if (hash1 != hash2 && hash1 != -1 && hash2 != -1) {
                goto return_ne;
            }
        }
#endif
        kind = __Pyx_PyUnicode_KIND(s1);
        if (kind != __Pyx_PyUnicode_KIND(s2)) {
            goto return_ne;
        }
        data1 = __Pyx_PyUnicode_DATA(s1);
        data2 = __Pyx_PyUnicode_DATA(s2);
        if (__Pyx_PyUnicode_READ(kind, data1, 0) != __Pyx_PyUnicode_READ(kind, data2, 0)) {
            goto return_ne;
        } else if (length == 1) {
            goto return_eq;
        } else {
            int result = memcmp(data1, data2, (size_t)(length * kind));
            return (equals == Py_EQ) ? (result == 0) : (result != 0);
        }
    } else if ((s1 == Py_None) & s2_is_unicode) {
        goto return_ne;
    } else if ((s2 == Py_None) & s1_is_unicode) {
        goto return_ne;
    } else {
        int result;
        PyObject* py_result = PyObject_RichCompare(s1, s2, equals);
        if (!py_result)
            return -1;
        result = __Pyx_PyObject_IsTrue(py_result);
        Py_DECREF(py_result);
        return result;
    }
return_eq:
    return (equals == Py_EQ);
return_ne:
    return (equals == Py_NE);
#endif
}

/* fastcall */
#if CYTHON_METH_FASTCALL
static CYTHON_INLINE PyObject * __Pyx_GetKwValue_FASTCALL(PyObject *kwnames, PyObject *const *kwvalues, PyObject *s)
{
    Py_ssize_t i, n = __Pyx_PyTuple_GET_SIZE(kwnames);
    #if !CYTHON_ASSUME_SAFE_SIZE
    if (unlikely(n == -1)) return NULL;
    #endif
    for (i = 0; i < n; i++)
    {
        PyObject *namei = __Pyx_PyTuple_GET_ITEM(kwnames, i);
        #if !CYTHON_ASSUME_SAFE_MACROS
        if (unlikely(!namei)) return NULL;
        #endif
        if (s == namei) return kwvalues[i];
    }
    for (i = 0; i < n; i++)
    {
        PyObject *namei = __Pyx_PyTuple_GET_ITEM(kwnames, i);
        #if !CYTHON_ASSUME_SAFE_MACROS
        if (unlikely(!namei)) return NULL;
        #endif
        int eq = __Pyx_PyUnicode_Equals(s, namei, Py_EQ);
        if (unlikely(eq != 0)) {
            if (unlikely(eq < 0)) return NULL;
            return kwvalues[i];
        }
    }
    return NULL;
}
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX >= 0x030d0000 || CYTHON_COMPILING_IN_LIMITED_API
CYTHON_UNUSED static PyObject *__Pyx_KwargsAsDict_FASTCALL(PyObject *kwnames, PyObject *const *kwvalues) {
    Py_ssize_t i, nkwargs;
    PyObject *dict;
#if !CYTHON_ASSUME_SAFE_SIZE
    nkwargs = PyTuple_Size(kwnames);
    if (unlikely(nkwargs < 0)) return NULL;
#else
    nkwargs = PyTuple_GET_SIZE(kwnames);
#endif
    dict = PyDict_New();
    if (unlikely(!dict))
        return NULL;
    for (i=0; i<nkwargs; i++) {
#if !CYTHON_ASSUME_SAFE_MACROS
        PyObject *key = PyTuple_GetItem(kwnames, i);
        if (!key) goto bad;
#else
        PyObject *key = PyTuple_GET_ITEM(kwnames, i);
#endif
        if (unlikely(PyDict_SetItem(dict, key, kwvalues[i]) < 0))
            goto bad;
    }
    return dict;
bad:
    Py_DECREF(dict);
    return NULL;
}
#endif
#endif

/* RaiseDoubleKeywords */
static void __Pyx_RaiseDoubleKeywordsError(
    const char* func_name,
    PyObject* kw_name)
{
    PyErr_Format(PyExc_TypeError,
        "%s() got multiple values for keyword argument '%U'", func_name, kw_name);
}

/* PyFunctionFastCall */
#if CYTHON_FAST_PYCALL && !CYTHON_VECTORCALL
static PyObject* __Pyx_PyFunction_FastCallNoKw(PyCodeObject *co, PyObject *const *args, Py_ssize_t na,
                                               PyObject *globals) {
    PyFrameObject *f;
    PyThreadState *tstate = __Pyx_PyThreadState_Current;
    PyObject **fastlocals;
    Py_ssize_t i;
    PyObject *result;
    assert(globals != NULL);
    /* XXX Perhaps we should create a specialized
       PyFrame_New() that doesn't take locals, but does
       take builtins without sanity checking them.
       */
    assert(tstate != NULL);
    f = PyFrame_New(tstate, co, globals, NULL);
    if (f == NULL) {
        return NULL;
    }
    fastlocals = __Pyx_PyFrame_GetLocalsplus(f);
    for (i = 0; i < na; i++) {
        Py_INCREF(*args);
        fastlocals[i] = *args++;
    }
    result = PyEval_EvalFrameEx(f,0);
    ++tstate->recursion_depth;
    Py_DECREF(f);
    --tstate->recursion_depth;
    return result;
}
static PyObject *__Pyx_PyFunction_FastCallDict(PyObject *func, PyObject *const *args, Py_ssize_t nargs, PyObject *kwargs) {
    PyCodeObject *co = (PyCodeObject *)PyFunction_GET_CODE(func);
    PyObject *globals = PyFunction_GET_GLOBALS(func);
    PyObject *argdefs = PyFunction_GET_DEFAULTS(func);
    PyObject *closure;
    PyObject *kwdefs;
    PyObject *kwtuple, **k;
    PyObject **d;
    Py_ssize_t nd;
    Py_ssize_t nk;
    PyObject *result;
    assert(kwargs == NULL || PyDict_Check(kwargs));
    nk = kwargs ? PyDict_Size(kwargs) : 0;
    if (unlikely(Py_EnterRecursiveCall(" while calling a Python object"))) {
        return NULL;
    }
    if (
            co->co_kwonlyargcount == 0 &&
            likely(kwargs == NULL || nk == 0) &&
            co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE)) {
        if (argdefs == NULL && co->co_argcount == nargs) {
            result = __Pyx_PyFunction_FastCallNoKw(co, args, nargs, globals);
            goto done;
        }
        else if (nargs == 0 && argdefs != NULL
                 && co->co_argcount == Py_SIZE(argdefs)) {
            /* function called with no arguments, but all parameters have
               a default value: use default values as arguments .*/
            args = &PyTuple_GET_ITEM(argdefs, 0);
            result =__Pyx_PyFunction_FastCallNoKw(co, args, Py_SIZE(argdefs), globals);
            goto done;
        }
    }
    if (kwargs != NULL) {
        Py_ssize_t pos, i;
        kwtuple = PyTuple_New(2 * nk);
        if (kwtuple == NULL) {
            result = NULL;
            goto done;
        }
        k = &PyTuple_GET_ITEM(kwtuple, 0);
        pos = i = 0;
        while (PyDict_Next(kwargs, &pos, &k[i], &k[i+1])) {
            Py_INCREF(k[i]);
            Py_INCREF(k[i+1]);
            i += 2;
        }
        nk = i / 2;
    }
    else {
        kwtuple = NULL;
        k = NULL;
    }
    closure = PyFunction_GET_CLOSURE(func);
    kwdefs = PyFunction_GET_KW_DEFAULTS(func);
    if (argdefs != NULL) {
        d = &PyTuple_GET_ITEM(argdefs, 0);
        nd = Py_SIZE(argdefs);
    }
    else {
        d = NULL;
        nd = 0;
    }
    result = PyEval_EvalCodeEx((PyObject*)co, globals, (PyObject *)NULL,
                               args, (int)nargs,
                               k, (int)nk,
                               d, (int)nd, kwdefs, closure);
    Py_XDECREF(kwtuple);
done:
    Py_LeaveRecursiveCall();
    return result;
}
#endif

/* PyObjectCall */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject* __Pyx_PyObject_Call(PyObject *func, PyObject *arg, PyObject *kw) {
    PyObject *result;
    ternaryfunc call = Py_TYPE(func)->tp_call;
    if (unlikely(!call))
        return PyObject_Call(func, arg, kw);
    if (unlikely(Py_EnterRecursiveCall(" while calling a Python object")))
        return NULL;
    result = (*call)(func, arg, kw);
    Py_LeaveRecursiveCall();
    if (unlikely(!result) && unlikely(!PyErr_Occurred())) {
        PyErr_SetString(
            PyExc_SystemError,
            "NULL result without error in PyObject_Call");
    }
    return result;
}
#endif

/* PyObjectCallMethO */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallMethO(PyObject *func, PyObject *arg) {
    PyObject *self, *result;
    PyCFunction cfunc;
    cfunc = __Pyx_CyOrPyCFunction_GET_FUNCTION(func);
    self = __Pyx_CyOrPyCFunction_GET_SELF(func);
    if (unlikely(Py_EnterRecursiveCall(" while calling a Python object")))
        return NULL;
    result = cfunc(self, arg);
    Py_LeaveRecursiveCall();
    if (unlikely(!result) && unlikely(!PyErr_Occurred())) {
        PyErr_SetString(
            PyExc_SystemError,
            "NULL result without error in PyObject_Call");
    }
    return result;
}
#endif

/* PyObjectFastCall */
#if PY_VERSION_HEX < 0x03090000 || CYTHON_COMPILING_IN_LIMITED_API
static PyObject* __Pyx_PyObject_FastCall_fallback(PyObject *func, PyObject * const*args, size_t nargs, PyObject *kwargs) {
    PyObject *argstuple;
    PyObject *result = 0;
    size_t i;
    argstuple = PyTuple_New((Py_ssize_t)nargs);
    if (unlikely(!argstuple)) return NULL;
    for (i = 0; i < nargs; i++) {
        Py_INCREF(args[i]);
        if (__Pyx_PyTuple_SET_ITEM(argstuple, (Py_ssize_t)i, args[i]) != (0)) goto bad;
    }
    result = __Pyx_PyObject_Call(func, argstuple, kwargs);
  bad:
    Py_DECREF(argstuple);
    return result;
}
#endif
#if CYTHON_VECTORCALL && !CYTHON_COMPILING_IN_LIMITED_API
  #if PY_VERSION_HEX < 0x03090000
    #define __Pyx_PyVectorcall_Function(callable) _PyVectorcall_Function(callable)
  #elif CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE vectorcallfunc __Pyx_PyVectorcall_Function(PyObject *callable) {
    PyTypeObject *tp = Py_TYPE(callable);
    #if defined(__Pyx_CyFunction_USED)
    if (__Pyx_CyFunction_CheckExact(callable)) {
        return __Pyx_CyFunction_func_vectorcall(callable);
    }
    #endif
    if (!PyType_HasFeature(tp, Py_TPFLAGS_HAVE_VECTORCALL)) {
        return NULL;
    }
    assert(PyCallable_Check(callable));
    Py_ssize_t offset = tp->tp_vectorcall_offset;
    assert(offset > 0);
    vectorcallfunc ptr;
    memcpy(&ptr, (char *) callable + offset, sizeof(ptr));
    return ptr;
}
  #else
    #define __Pyx_PyVectorcall_Function(callable) PyVectorcall_Function(callable)
  #endif
#endif
static CYTHON_INLINE PyObject* __Pyx_PyObject_FastCallDict(PyObject *func, PyObject *const *args, size_t _nargs, PyObject *kwargs) {
    Py_ssize_t nargs = __Pyx_PyVectorcall_NARGS(_nargs);
#if CYTHON_COMPILING_IN_CPYTHON
    if (nargs == 0 && kwargs == NULL) {
        if (__Pyx_CyOrPyCFunction_Check(func) && likely( __Pyx_CyOrPyCFunction_GET_FLAGS(func) & METH_NOARGS))
            return __Pyx_PyObject_CallMethO(func, NULL);
    }
    else if (nargs == 1 && kwargs == NULL) {
        if (__Pyx_CyOrPyCFunction_Check(func) && likely( __Pyx_CyOrPyCFunction_GET_FLAGS(func) & METH_O))
            return __Pyx_PyObject_CallMethO(func, args[0]);
    }
#endif
    #if PY_VERSION_HEX < 0x030800B1
    #if CYTHON_FAST_PYCCALL
    if (PyCFunction_Check(func)) {
        if (kwargs) {
            return _PyCFunction_FastCallDict(func, args, nargs, kwargs);
        } else {
            return _PyCFunction_FastCallKeywords(func, args, nargs, NULL);
        }
    }
    if (!kwargs && __Pyx_IS_TYPE(func, &PyMethodDescr_Type)) {
        return _PyMethodDescr_FastCallKeywords(func, args, nargs, NULL);
    }
    #endif
    #if CYTHON_FAST_PYCALL
    if (PyFunction_Check(func)) {
        return __Pyx_PyFunction_FastCallDict(func, args, nargs, kwargs);
    }
    #endif
    #endif
    if (kwargs == NULL) {
        #if CYTHON_VECTORCALL && !CYTHON_COMPILING_IN_LIMITED_API
        vectorcallfunc f = __Pyx_PyVectorcall_Function(func);
        if (f) {
            return f(func, args, _nargs, NULL);
        }
        #elif defined(__Pyx_CyFunction_USED) && CYTHON_BACKPORT_VECTORCALL
        if (__Pyx_CyFunction_CheckExact(func)) {
            __pyx_vectorcallfunc f = __Pyx_CyFunction_func_vectorcall(func);
            if (f) return f(func, args, _nargs, NULL);
        }
        #elif CYTHON_COMPILING_IN_LIMITED_API && CYTHON_VECTORCALL
        return PyObject_Vectorcall(func, args, _nargs, NULL);
        #endif
    }
    if (nargs == 0) {
        return __Pyx_PyObject_Call(func, __pyx_mstate_global->__pyx_empty_tuple, kwargs);
    }
    #if PY_VERSION_HEX >= 0x03090000 && !CYTHON_COMPILING_IN_LIMITED_API
    return PyObject_VectorcallDict(func, args, (size_t)nargs, kwargs);
    #else
    return __Pyx_PyObject_FastCall_fallback(func, args, (size_t)nargs, kwargs);
    #endif
}

/* UnpackUnboundCMethod */
#if CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX < 0x030C0000
static PyObject *__Pyx_SelflessCall(PyObject *method, PyObject *args, PyObject *kwargs) {
    PyObject *result;
    PyObject *selfless_args = PyTuple_GetSlice(args, 1, PyTuple_Size(args));
    if (unlikely(!selfless_args)) return NULL;
    result = PyObject_Call(method, selfless_args, kwargs);
    Py_DECREF(selfless_args);
    return result;
}
#elif CYTHON_COMPILING_IN_PYPY && PY_VERSION_HEX < 0x03090000
static PyObject *__Pyx_SelflessCall(PyObject *method, PyObject **args, Py_ssize_t nargs, PyObject *kwnames) {
        return _PyObject_Vectorcall
            (method, args ? args+1 : NULL, nargs ? nargs-1 : 0, kwnames);
}
#else
static PyObject *__Pyx_SelflessCall(PyObject *method, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames) {
    return
#if PY_VERSION_HEX < 0x03090000
    _PyObject_Vectorcall
#else
    PyObject_Vectorcall
#endif
        (method, args ? args+1 : NULL, nargs ? (size_t) nargs-1 : 0, kwnames);
}
#endif
static PyMethodDef __Pyx_UnboundCMethod_Def = {
     "CythonUnboundCMethod",
     __PYX_REINTERPRET_FUNCION(PyCFunction, __Pyx_SelflessCall),
#if CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX < 0x030C0000
     METH_VARARGS | METH_KEYWORDS,
#else
     METH_FASTCALL | METH_KEYWORDS,
#endif
     NULL
};
static int __Pyx_TryUnpackUnboundCMethod(__Pyx_CachedCFunction* target) {
    PyObject *method, *result=NULL;
    method = __Pyx_PyObject_GetAttrStr(target->type, *target->method_name);
    if (unlikely(!method))
        return -1;
    result = method;
#if CYTHON_COMPILING_IN_CPYTHON
    if (likely(__Pyx_TypeCheck(method, &PyMethodDescr_Type)))
    {
        PyMethodDescrObject *descr = (PyMethodDescrObject*) method;
        target->func = descr->d_method->ml_meth;
        target->flag = descr->d_method->ml_flags & ~(METH_CLASS | METH_STATIC | METH_COEXIST | METH_STACKLESS);
    } else
#endif
#if CYTHON_COMPILING_IN_PYPY
#else
    if (PyCFunction_Check(method))
#endif
    {
        PyObject *self;
        int self_found;
#if CYTHON_COMPILING_IN_LIMITED_API || CYTHON_COMPILING_IN_PYPY
        self = PyObject_GetAttrString(method, "__self__");
        if (!self) {
            PyErr_Clear();
        }
#else
        self = PyCFunction_GET_SELF(method);
#endif
        self_found = (self && self != Py_None);
#if CYTHON_COMPILING_IN_LIMITED_API || CYTHON_COMPILING_IN_PYPY
        Py_XDECREF(self);
#endif
        if (self_found) {
            PyObject *unbound_method = PyCFunction_New(&__Pyx_UnboundCMethod_Def, method);
            if (unlikely(!unbound_method)) return -1;
            Py_DECREF(method);
            result = unbound_method;
        }
    }
#if !CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    if (unlikely(target->method)) {
        Py_DECREF(result);
    } else
#endif
    target->method = result;
    return 0;
}

/* CallUnboundCMethod2 */
#if CYTHON_COMPILING_IN_CPYTHON
static CYTHON_INLINE PyObject *__Pyx_CallUnboundCMethod2(__Pyx_CachedCFunction *cfunc, PyObject *self, PyObject *arg1, PyObject *arg2) {
    int was_initialized = __Pyx_CachedCFunction_GetAndSetInitializing(cfunc);
    if (likely(was_initialized == 2 && cfunc->func)) {
        PyObject *args[2] = {arg1, arg2};
        if (cfunc->flag == METH_FASTCALL) {
            return __Pyx_CallCFunctionFast(cfunc, self, args, 2);
        }
        if (cfunc->flag == (METH_FASTCALL | METH_KEYWORDS))
            return __Pyx_CallCFunctionFastWithKeywords(cfunc, self, args, 2, NULL);
    }
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    else if (unlikely(was_initialized == 1)) {
        __Pyx_CachedCFunction tmp_cfunc = {
#ifndef __cplusplus
            0
#endif
        };
        tmp_cfunc.type = cfunc->type;
        tmp_cfunc.method_name = cfunc->method_name;
        return __Pyx__CallUnboundCMethod2(&tmp_cfunc, self, arg1, arg2);
    }
#endif
    PyObject *result = __Pyx__CallUnboundCMethod2(cfunc, self, arg1, arg2);
    __Pyx_CachedCFunction_SetFinishedInitializing(cfunc);
    return result;
}
#endif
static PyObject* __Pyx__CallUnboundCMethod2(__Pyx_CachedCFunction* cfunc, PyObject* self, PyObject* arg1, PyObject* arg2){
    if (unlikely(!cfunc->func && !cfunc->method) && unlikely(__Pyx_TryUnpackUnboundCMethod(cfunc) < 0)) return NULL;
#if CYTHON_COMPILING_IN_CPYTHON
    if (cfunc->func && (cfunc->flag & METH_VARARGS)) {
        PyObject *result = NULL;
        PyObject *args = PyTuple_New(2);
        if (unlikely(!args)) return NULL;
        Py_INCREF(arg1);
        PyTuple_SET_ITEM(args, 0, arg1);
        Py_INCREF(arg2);
        PyTuple_SET_ITEM(args, 1, arg2);
        if (cfunc->flag & METH_KEYWORDS)
            result = __Pyx_CallCFunctionWithKeywords(cfunc, self, args, NULL);
        else
            result = __Pyx_CallCFunction(cfunc, self, args);
        Py_DECREF(args);
        return result;
    }
#endif
    {
        PyObject *args[4] = {NULL, self, arg1, arg2};
        return __Pyx_PyObject_FastCall(cfunc->method, args+1, 3 | __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET);
    }
}

/* ParseKeywords */
static int __Pyx_ValidateDuplicatePosArgs(
    PyObject *kwds,
    PyObject ** const argnames[],
    PyObject ** const *first_kw_arg,
    const char* function_name)
{
    PyObject ** const *name = argnames;
    while (name != first_kw_arg) {
        PyObject *key = **name;
        int found = PyDict_Contains(kwds, key);
        if (unlikely(found)) {
            if (found == 1) __Pyx_RaiseDoubleKeywordsError(function_name, key);
            goto bad;
        }
        name++;
    }
    return 0;
bad:
    return -1;
}
#if CYTHON_USE_UNICODE_INTERNALS
static CYTHON_INLINE int __Pyx_UnicodeKeywordsEqual(PyObject *s1, PyObject *s2) {
    int kind;
    Py_ssize_t len = PyUnicode_GET_LENGTH(s1);
    if (len != PyUnicode_GET_LENGTH(s2)) return 0;
    kind = PyUnicode_KIND(s1);
    if (kind != PyUnicode_KIND(s2)) return 0;
    const void *data1 = PyUnicode_DATA(s1);
    const void *data2 = PyUnicode_DATA(s2);
    return (memcmp(data1, data2, (size_t) len * (size_t) kind) == 0);
}
#endif
static int __Pyx_MatchKeywordArg_str(
    PyObject *key,
    PyObject ** const argnames[],
    PyObject ** const *first_kw_arg,
    size_t *index_found,
    const char *function_name)
{
    PyObject ** const *name;
    #if CYTHON_USE_UNICODE_INTERNALS
    Py_hash_t key_hash = ((PyASCIIObject*)key)->hash;
    if (unlikely(key_hash == -1)) {
        key_hash = PyObject_Hash(key);
        if (unlikely(key_hash == -1))
            goto bad;
    }
    #endif
    name = first_kw_arg;
    while (*name) {
        PyObject *name_str = **name;
        #if CYTHON_USE_UNICODE_INTERNALS
        if (key_hash == ((PyASCIIObject*)name_str)->hash && __Pyx_UnicodeKeywordsEqual(name_str, key)) {
            *index_found = (size_t) (name - argnames);
            return 1;
        }
        #else
        #if CYTHON_ASSUME_SAFE_SIZE
        if (PyUnicode_GET_LENGTH(name_str) == PyUnicode_GET_LENGTH(key))
        #endif
        {
            int cmp = PyUnicode_Compare(name_str, key);
            if (cmp < 0 && unlikely(PyErr_Occurred())) goto bad;
            if (cmp == 0) {
                *index_found = (size_t) (name - argnames);
                return 1;
            }
        }
        #endif
        name++;
    }
    name = argnames;
    while (name != first_kw_arg) {
        PyObject *name_str = **name;
        #if CYTHON_USE_UNICODE_INTERNALS
        if (unlikely(key_hash == ((PyASCIIObject*)name_str)->hash)) {
            if (__Pyx_UnicodeKeywordsEqual(name_str, key))
                goto arg_passed_twice;
        }
        #else
        #if CYTHON_ASSUME_SAFE_SIZE
        if (PyUnicode_GET_LENGTH(name_str) == PyUnicode_GET_LENGTH(key))
        #endif
        {
            if (unlikely(name_str == key)) goto arg_passed_twice;
            int cmp = PyUnicode_Compare(name_str, key);
            if (cmp < 0 && unlikely(PyErr_Occurred())) goto bad;
            if (cmp == 0) goto arg_passed_twice;
        }
        #endif
        name++;
    }
    return 0;
arg_passed_twice:
    __Pyx_RaiseDoubleKeywordsError(function_name, key);
    goto bad;
bad:
    return -1;
}
static int __Pyx_MatchKeywordArg_nostr(
    PyObject *key,
    PyObject ** const argnames[],
    PyObject ** const *first_kw_arg,
    size_t *index_found,
    const char *function_name)
{
    PyObject ** const *name;
    if (unlikely(!PyUnicode_Check(key))) goto invalid_keyword_type;
    name = first_kw_arg;
    while (*name) {
        int cmp = PyObject_RichCompareBool(**name, key, Py_EQ);
        if (cmp == 1) {
            *index_found = (size_t) (name - argnames);
            return 1;
        }
        if (unlikely(cmp == -1)) goto bad;
        name++;
    }
    name = argnames;
    while (name != first_kw_arg) {
        int cmp = PyObject_RichCompareBool(**name, key, Py_EQ);
        if (unlikely(cmp != 0)) {
            if (cmp == 1) goto arg_passed_twice;
            else goto bad;
        }
        name++;
    }
    return 0;
arg_passed_twice:
    __Pyx_RaiseDoubleKeywordsError(function_name, key);
    goto bad;
invalid_keyword_type:
    PyErr_Format(PyExc_TypeError,
        "%.200s() keywords must be strings", function_name);
    goto bad;
bad:
    return -1;
}
static CYTHON_INLINE int __Pyx_MatchKeywordArg(
    PyObject *key,
    PyObject ** const argnames[],
    PyObject ** const *first_kw_arg,
    size_t *index_found,
    const char *function_name)
{
    return likely(PyUnicode_CheckExact(key)) ?
        __Pyx_MatchKeywordArg_str(key, argnames, first_kw_arg, index_found, function_name) :
        __Pyx_MatchKeywordArg_nostr(key, argnames, first_kw_arg, index_found, function_name);
}
static void __Pyx_RejectUnknownKeyword(
    PyObject *kwds,
    PyObject ** const argnames[],
    PyObject ** const *first_kw_arg,
    const char *function_name)
{
    Py_ssize_t pos = 0;
    PyObject *key = NULL;
    __Pyx_BEGIN_CRITICAL_SECTION(kwds);
    while (PyDict_Next(kwds, &pos, &key, NULL)) {
        PyObject** const *name = first_kw_arg;
        while (*name && (**name != key)) name++;
        if (!*name) {
            #if CYTHON_AVOID_BORROWED_REFS
            Py_INCREF(key);
            #endif
            size_t index_found = 0;
            int cmp = __Pyx_MatchKeywordArg(key, argnames, first_kw_arg, &index_found, function_name);
            if (cmp != 1) {
                if (cmp == 0) {
                    PyErr_Format(PyExc_TypeError,
                        "%s() got an unexpected keyword argument '%U'",
                        function_name, key);
                }
                #if CYTHON_AVOID_BORROWED_REFS
                Py_DECREF(key);
                #endif
                break;
            }
            #if CYTHON_AVOID_BORROWED_REFS
            Py_DECREF(key);
            #endif
        }
    }
    __Pyx_END_CRITICAL_SECTION();
    assert(PyErr_Occurred());
}
static int __Pyx_ParseKeywordDict(
    PyObject *kwds,
    PyObject ** const argnames[],
    PyObject *values[],
    Py_ssize_t num_pos_args,
    Py_ssize_t num_kwargs,
    const char* function_name,
    int ignore_unknown_kwargs)
{
    PyObject** const *name;
    PyObject** const *first_kw_arg = argnames + num_pos_args;
    Py_ssize_t extracted = 0;
#if !CYTHON_COMPILING_IN_PYPY || defined(PyArg_ValidateKeywordArguments)
    if (unlikely(!PyArg_ValidateKeywordArguments(kwds))) return -1;
#endif
    name = first_kw_arg;
    while (*name && num_kwargs > extracted) {
        PyObject * key = **name;
        PyObject *value;
        int found = 0;
        #if __PYX_LIMITED_VERSION_HEX >= 0x030d0000
        found = PyDict_GetItemRef(kwds, key, &value);
        #else
        value = PyDict_GetItemWithError(kwds, key);
        if (value) {
            Py_INCREF(value);
            found = 1;
        } else {
            if (unlikely(PyErr_Occurred())) goto bad;
        }
        #endif
        if (found) {
            if (unlikely(found < 0)) goto bad;
            values[name-argnames] = value;
            extracted++;
        }
        name++;
    }
    if (num_kwargs > extracted) {
        if (ignore_unknown_kwargs) {
            if (unlikely(__Pyx_ValidateDuplicatePosArgs(kwds, argnames, first_kw_arg, function_name) == -1))
                goto bad;
        } else {
            __Pyx_RejectUnknownKeyword(kwds, argnames, first_kw_arg, function_name);
            goto bad;
        }
    }
    return 0;
bad:
    return -1;
}
static int __Pyx_ParseKeywordDictToDict(
    PyObject *kwds,
    PyObject ** const argnames[],
    PyObject *kwds2,
    PyObject *values[],
    Py_ssize_t num_pos_args,
    const char* function_name)
{
    PyObject** const *name;
    PyObject** const *first_kw_arg = argnames + num_pos_args;
    Py_ssize_t len;
#if !CYTHON_COMPILING_IN_PYPY || defined(PyArg_ValidateKeywordArguments)
    if (unlikely(!PyArg_ValidateKeywordArguments(kwds))) return -1;
#endif
    if (PyDict_Update(kwds2, kwds) < 0) goto bad;
    name = first_kw_arg;
    while (*name) {
        PyObject *key = **name;
        PyObject *value;
#if !CYTHON_COMPILING_IN_LIMITED_API && (PY_VERSION_HEX >= 0x030d00A2 || defined(PyDict_Pop))
        int found = PyDict_Pop(kwds2, key, &value);
        if (found) {
            if (unlikely(found < 0)) goto bad;
            values[name-argnames] = value;
        }
#elif __PYX_LIMITED_VERSION_HEX >= 0x030d0000
        int found = PyDict_GetItemRef(kwds2, key, &value);
        if (found) {
            if (unlikely(found < 0)) goto bad;
            values[name-argnames] = value;
            if (unlikely(PyDict_DelItem(kwds2, key) < 0)) goto bad;
        }
#else
    #if CYTHON_COMPILING_IN_CPYTHON
        value = _PyDict_Pop(kwds2, key, kwds2);
    #else
        value = __Pyx_CallUnboundCMethod2(&__pyx_mstate_global->__pyx_umethod_PyDict_Type_pop, kwds2, key, kwds2);
    #endif
        if (value == kwds2) {
            Py_DECREF(value);
        } else {
            if (unlikely(!value)) goto bad;
            values[name-argnames] = value;
        }
#endif
        name++;
    }
    len = PyDict_Size(kwds2);
    if (len > 0) {
        return __Pyx_ValidateDuplicatePosArgs(kwds, argnames, first_kw_arg, function_name);
    } else if (unlikely(len == -1)) {
        goto bad;
    }
    return 0;
bad:
    return -1;
}
static int __Pyx_ParseKeywordsTuple(
    PyObject *kwds,
    PyObject * const *kwvalues,
    PyObject ** const argnames[],
    PyObject *kwds2,
    PyObject *values[],
    Py_ssize_t num_pos_args,
    Py_ssize_t num_kwargs,
    const char* function_name,
    int ignore_unknown_kwargs)
{
    PyObject *key = NULL;
    PyObject** const * name;
    PyObject** const *first_kw_arg = argnames + num_pos_args;
    for (Py_ssize_t pos = 0; pos < num_kwargs; pos++) {
#if CYTHON_AVOID_BORROWED_REFS
        key = __Pyx_PySequence_ITEM(kwds, pos);
#else
        key = __Pyx_PyTuple_GET_ITEM(kwds, pos);
#endif
#if !CYTHON_ASSUME_SAFE_MACROS
        if (unlikely(!key)) goto bad;
#endif
        name = first_kw_arg;
        while (*name && (**name != key)) name++;
        if (*name) {
            PyObject *value = kwvalues[pos];
            values[name-argnames] = __Pyx_NewRef(value);
        } else {
            size_t index_found = 0;
            int cmp = __Pyx_MatchKeywordArg(key, argnames, first_kw_arg, &index_found, function_name);
            if (cmp == 1) {
                PyObject *value = kwvalues[pos];
                values[index_found] = __Pyx_NewRef(value);
            } else {
                if (unlikely(cmp == -1)) goto bad;
                if (kwds2) {
                    PyObject *value = kwvalues[pos];
                    if (unlikely(PyDict_SetItem(kwds2, key, value))) goto bad;
                } else if (!ignore_unknown_kwargs) {
                    goto invalid_keyword;
                }
            }
        }
        #if CYTHON_AVOID_BORROWED_REFS
        Py_DECREF(key);
        key = NULL;
        #endif
    }
    return 0;
invalid_keyword:
    PyErr_Format(PyExc_TypeError,
        "%s() got an unexpected keyword argument '%U'",
        function_name, key);
    goto bad;
bad:
    #if CYTHON_AVOID_BORROWED_REFS
    Py_XDECREF(key);
    #endif
    return -1;
}
static int __Pyx_ParseKeywords(
    PyObject *kwds,
    PyObject * const *kwvalues,
    PyObject ** const argnames[],
    PyObject *kwds2,
    PyObject *values[],
    Py_ssize_t num_pos_args,
    Py_ssize_t num_kwargs,
    const char* function_name,
    int ignore_unknown_kwargs)
{
    if (CYTHON_METH_FASTCALL && likely(PyTuple_Check(kwds)))
        return __Pyx_ParseKeywordsTuple(kwds, kwvalues, argnames, kwds2, values, num_pos_args, num_kwargs, function_name, ignore_unknown_kwargs);
    else if (kwds2)
        return __Pyx_ParseKeywordDictToDict(kwds, argnames, kwds2, values, num_pos_args, function_name);
    else
        return __Pyx_ParseKeywordDict(kwds, argnames, values, num_pos_args, num_kwargs, function_name, ignore_unknown_kwargs);
}

/* RaiseArgTupleInvalid */
static void __Pyx_RaiseArgtupleInvalid(
    const char* func_name,
    int exact,
    Py_ssize_t num_min,
    Py_ssize_t num_max,
    Py_ssize_t num_found)
{
    Py_ssize_t num_expected;
    const char *more_or_less;
    if (num_found < num_min) {
        num_expected = num_min;
        more_or_less = "at least";
    } else {
        num_expected = num_max;
        more_or_less = "at most";
    }
    if (exact) {
        more_or_less = "exactly";
    }
    PyErr_Format(PyExc_TypeError,
                 "%.200s() takes %.8s %" CYTHON_FORMAT_SSIZE_T "d positional argument%.1s (%" CYTHON_FORMAT_SSIZE_T "d given)",
                 func_name, more_or_less, num_expected,
                 (num_expected == 1) ? "" : "s", num_found);
}

/* PyObjectFastCallMethod */
#if !CYTHON_VECTORCALL || PY_VERSION_HEX < 0x03090000
static PyObject *__Pyx_PyObject_FastCallMethod(PyObject *name, PyObject *const *args, size_t nargsf) {
    PyObject *result;
    PyObject *attr = PyObject_GetAttr(args[0], name);
    if (unlikely(!attr))
        return NULL;
    result = __Pyx_PyObject_FastCall(attr, args+1, nargsf - 1);
    Py_DECREF(attr);
    return result;
}
#endif

/* GetItemInt */
static PyObject *__Pyx_GetItemInt_Generic(PyObject *o, PyObject* j) {
    PyObject *r;
    if (unlikely(!j)) return NULL;
    r = PyObject_GetItem(o, j);
    Py_DECREF(j);
    return r;
}
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_List_Fast(PyObject *o, Py_ssize_t i,
                                                              CYTHON_NCP_UNUSED int wraparound,
                                                              CYTHON_NCP_UNUSED int boundscheck) {
#if CYTHON_ASSUME_SAFE_MACROS && CYTHON_ASSUME_SAFE_SIZE && !CYTHON_AVOID_BORROWED_REFS && !CYTHON_AVOID_THREAD_UNSAFE_BORROWED_REFS
    Py_ssize_t wrapped_i = i;
    if (wraparound & unlikely(i < 0)) {
        wrapped_i += PyList_GET_SIZE(o);
    }
    if ((!boundscheck) || likely(__Pyx_is_valid_index(wrapped_i, PyList_GET_SIZE(o)))) {
        PyObject *r = PyList_GET_ITEM(o, wrapped_i);
        Py_INCREF(r);
        return r;
    }
    return __Pyx_GetItemInt_Generic(o, PyLong_FromSsize_t(i));
#else
    return PySequence_GetItem(o, i);
#endif
}
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_Tuple_Fast(PyObject *o, Py_ssize_t i,
                                                              CYTHON_NCP_UNUSED int wraparound,
                                                              CYTHON_NCP_UNUSED int boundscheck) {
#if CYTHON_ASSUME_SAFE_MACROS && CYTHON_ASSUME_SAFE_SIZE && !CYTHON_AVOID_BORROWED_REFS
    Py_ssize_t wrapped_i = i;
    if (wraparound & unlikely(i < 0)) {
        wrapped_i += PyTuple_GET_SIZE(o);
    }
    if ((!boundscheck) || likely(__Pyx_is_valid_index(wrapped_i, PyTuple_GET_SIZE(o)))) {
        PyObject *r = PyTuple_GET_ITEM(o, wrapped_i);
        Py_INCREF(r);
        return r;
    }
    return __Pyx_GetItemInt_Generic(o, PyLong_FromSsize_t(i));
#else
    return PySequence_GetItem(o, i);
#endif
}
static CYTHON_INLINE PyObject *__Pyx_GetItemInt_Fast(PyObject *o, Py_ssize_t i, int is_list,
                                                     CYTHON_NCP_UNUSED int wraparound,
                                                     CYTHON_NCP_UNUSED int boundscheck) {
#if CYTHON_ASSUME_SAFE_MACROS && CYTHON_ASSUME_SAFE_SIZE && !CYTHON_AVOID_BORROWED_REFS && CYTHON_USE_TYPE_SLOTS
    if (is_list || PyList_CheckExact(o)) {
        Py_ssize_t n = ((!wraparound) | likely(i >= 0)) ? i : i + PyList_GET_SIZE(o);
        if ((!boundscheck) || (likely(__Pyx_is_valid_index(n, PyList_GET_SIZE(o))))) {
            return __Pyx_PyList_GetItemRef(o, n);
        }
    }
    else if (PyTuple_CheckExact(o)) {
        Py_ssize_t n = ((!wraparound) | likely(i >= 0)) ? i : i + PyTuple_GET_SIZE(o);
        if ((!boundscheck) || likely(__Pyx_is_valid_index(n, PyTuple_GET_SIZE(o)))) {
            PyObject *r = PyTuple_GET_ITEM(o, n);
            Py_INCREF(r);
            return r;
        }
    } else {
        PyMappingMethods *mm = Py_TYPE(o)->tp_as_mapping;
        PySequenceMethods *sm = Py_TYPE(o)->tp_as_sequence;
        if (mm && mm->mp_subscript) {
            PyObject *r, *key = PyLong_FromSsize_t(i);
            if (unlikely(!key)) return NULL;
            r = mm->mp_subscript(o, key);
            Py_DECREF(key);
            return r;
        }
        if (likely(sm && sm->sq_item)) {
            if (wraparound && unlikely(i < 0) && likely(sm->sq_length)) {
                Py_ssize_t l = sm->sq_length(o);
                if (likely(l >= 0)) {
                    i += l;
                } else {
                    if (!PyErr_ExceptionMatches(PyExc_OverflowError))
                        return NULL;
                    PyErr_Clear();
                }
            }
            return sm->sq_item(o, i);
        }
    }
#else
    if (is_list || !PyMapping_Check(o)) {
        return PySequence_GetItem(o, i);
    }
#endif
    return __Pyx_GetItemInt_Generic(o, PyLong_FromSsize_t(i));
}

/* LimitedApiGetTypeDict */
#if CYTHON_COMPILING_IN_LIMITED_API
static Py_ssize_t __Pyx_GetTypeDictOffset(void) {
    PyObject *tp_dictoffset_o;
    Py_ssize_t tp_dictoffset;
    tp_dictoffset_o = PyObject_GetAttrString((PyObject*)(&PyType_Type), "__dictoffset__");
    if (unlikely(!tp_dictoffset_o)) return -1;
    tp_dictoffset = PyLong_AsSsize_t(tp_dictoffset_o);
    Py_DECREF(tp_dictoffset_o);
    if (unlikely(tp_dictoffset == 0)) {
        PyErr_SetString(
            PyExc_TypeError,
            "'type' doesn't have a dictoffset");
        return -1;
    } else if (unlikely(tp_dictoffset < 0)) {
        PyErr_SetString(
            PyExc_TypeError,
            "'type' has an unexpected negative dictoffset. "
            "Please report this as Cython bug");
        return -1;
    }
    return tp_dictoffset;
}
static PyObject *__Pyx_GetTypeDict(PyTypeObject *tp) {
    static Py_ssize_t tp_dictoffset = 0;
    if (unlikely(tp_dictoffset == 0)) {
        tp_dictoffset = __Pyx_GetTypeDictOffset();
        if (unlikely(tp_dictoffset == -1 && PyErr_Occurred())) {
            tp_dictoffset = 0; // try again next time?
            return NULL;
        }
    }
    return *(PyObject**)((char*)tp + tp_dictoffset);
}
#endif

/* SetItemOnTypeDict */
static int __Pyx__SetItemOnTypeDict(PyTypeObject *tp, PyObject *k, PyObject *v) {
    int result;
    PyObject *tp_dict;
#if CYTHON_COMPILING_IN_LIMITED_API
    tp_dict = __Pyx_GetTypeDict(tp);
    if (unlikely(!tp_dict)) return -1;
#else
    tp_dict = tp->tp_dict;
#endif
    result = PyDict_SetItem(tp_dict, k, v);
    if (likely(!result)) {
        PyType_Modified(tp);
        if (unlikely(PyObject_HasAttr(v, __pyx_mstate_global->__pyx_n_u_set_name))) {
            PyObject *setNameResult = PyObject_CallMethodObjArgs(v, __pyx_mstate_global->__pyx_n_u_set_name,  (PyObject *) tp, k, NULL);
            if (!setNameResult) return -1;
            Py_DECREF(setNameResult);
        }
    }
    return result;
}

/* FixUpExtensionType */
static int __Pyx_fix_up_extension_type_from_spec(PyType_Spec *spec, PyTypeObject *type) {
#if __PYX_LIMITED_VERSION_HEX > 0x030900B1
    CYTHON_UNUSED_VAR(spec);
    CYTHON_UNUSED_VAR(type);
    CYTHON_UNUSED_VAR(__Pyx__SetItemOnTypeDict);
#else
    const PyType_Slot *slot = spec->slots;
    int changed = 0;
#if !CYTHON_COMPILING_IN_LIMITED_API
    while (slot && slot->slot && slot->slot != Py_tp_members)
        slot++;
    if (slot && slot->slot == Py_tp_members) {
#if !CYTHON_COMPILING_IN_CPYTHON
        const
#endif  // !CYTHON_COMPILING_IN_CPYTHON)
            PyMemberDef *memb = (PyMemberDef*) slot->pfunc;
        while (memb && memb->name) {
            if (memb->name[0] == '_' && memb->name[1] == '_') {
                if (strcmp(memb->name, "__weaklistoffset__") == 0) {
                    assert(memb->type == T_PYSSIZET);
                    assert(memb->flags == READONLY);
                    type->tp_weaklistoffset = memb->offset;
                    changed = 1;
                }
                else if (strcmp(memb->name, "__dictoffset__") == 0) {
                    assert(memb->type == T_PYSSIZET);
                    assert(memb->flags == READONLY);
                    type->tp_dictoffset = memb->offset;
                    changed = 1;
                }
#if CYTHON_METH_FASTCALL
                else if (strcmp(memb->name, "__vectorcalloffset__") == 0) {
                    assert(memb->type == T_PYSSIZET);
                    assert(memb->flags == READONLY);
#if PY_VERSION_HEX >= 0x030800b4
                    type->tp_vectorcall_offset = memb->offset;
#else
                    type->tp_print = (printfunc) memb->offset;
#endif
                    changed = 1;
                }
#endif  // CYTHON_METH_FASTCALL
                else if (strcmp(memb->name, "__module__") == 0) {
                    PyObject *descr;
                    assert(memb->type == T_OBJECT);
                    assert(memb->flags == 0 || memb->flags == READONLY);
                    descr = PyDescr_NewMember(type, memb);
                    if (unlikely(!descr))
                        return -1;
                    int set_item_result = PyDict_SetItem(type->tp_dict, PyDescr_NAME(descr), descr);
                    Py_DECREF(descr);
                    if (unlikely(set_item_result < 0)) {
                        return -1;
                    }
                    changed = 1;
                }
            }
            memb++;
        }
    }
#endif  // !CYTHON_COMPILING_IN_LIMITED_API
    slot = spec->slots;
    while (slot && slot->slot && slot->slot != Py_tp_getset)
        slot++;
    if (slot && slot->slot == Py_tp_getset) {
        PyGetSetDef *getset = (PyGetSetDef*) slot->pfunc;
        while (getset && getset->name) {
            if (getset->name[0] == '_' && getset->name[1] == '_' && strcmp(getset->name, "__module__") == 0) {
                PyObject *descr = PyDescr_NewGetSet(type, getset);
                if (unlikely(!descr))
                    return -1;
                #if CYTHON_COMPILING_IN_LIMITED_API
                PyObject *pyname = PyUnicode_FromString(getset->name);
                if (unlikely(!pyname)) {
                    Py_DECREF(descr);
                    return -1;
                }
                int set_item_result = __Pyx_SetItemOnTypeDict(type, pyname, descr);
                Py_DECREF(pyname);
                #else
                CYTHON_UNUSED_VAR(__Pyx__SetItemOnTypeDict);
                int set_item_result = PyDict_SetItem(type->tp_dict, PyDescr_NAME(descr), descr);
                #endif
                Py_DECREF(descr);
                if (unlikely(set_item_result < 0)) {
                    return -1;
                }
                changed = 1;
            }
            ++getset;
        }
    }
    if (changed)
        PyType_Modified(type);
#endif  // PY_VERSION_HEX > 0x030900B1
    return 0;
}

/* FetchSharedCythonModule */
static PyObject *__Pyx_FetchSharedCythonABIModule(void) {
    return __Pyx_PyImport_AddModuleRef(__PYX_ABI_MODULE_NAME);
}

/* dict_setdefault */
static CYTHON_INLINE PyObject *__Pyx_PyDict_SetDefault(PyObject *d, PyObject *key, PyObject *default_value,
                                                       int is_safe_type) {
    PyObject* value;
    CYTHON_MAYBE_UNUSED_VAR(is_safe_type);
#if CYTHON_COMPILING_IN_LIMITED_API
    value = PyObject_CallMethod(d, "setdefault", "OO", key, default_value);
#elif PY_VERSION_HEX >= 0x030d0000
    PyDict_SetDefaultRef(d, key, default_value, &value);
#else
    value = PyDict_SetDefault(d, key, default_value);
    if (unlikely(!value)) return NULL;
    Py_INCREF(value);
#endif
    return value;
}

/* FetchCommonType */
#if __PYX_LIMITED_VERSION_HEX < 0x030C0000
static PyObject* __Pyx_PyType_FromMetaclass(PyTypeObject *metaclass, PyObject *module, PyType_Spec *spec, PyObject *bases) {
    PyObject *result = __Pyx_PyType_FromModuleAndSpec(module, spec, bases);
    if (result && metaclass) {
        PyObject *old_tp = (PyObject*)Py_TYPE(result);
    Py_INCREF((PyObject*)metaclass);
#if __PYX_LIMITED_VERSION_HEX >= 0x03090000
        Py_SET_TYPE(result, metaclass);
#else
        result->ob_type = metaclass;
#endif
        Py_DECREF(old_tp);
    }
    return result;
}
#else
#define __Pyx_PyType_FromMetaclass(me, mo, s, b) PyType_FromMetaclass(me, mo, s, b)
#endif
static int __Pyx_VerifyCachedType(PyObject *cached_type,
                               const char *name,
                               Py_ssize_t expected_basicsize) {
    Py_ssize_t basicsize;
    if (!PyType_Check(cached_type)) {
        PyErr_Format(PyExc_TypeError,
            "Shared Cython type %.200s is not a type object", name);
        return -1;
    }
    if (expected_basicsize == 0) {
        return 0; // size is inherited, nothing useful to check
    }
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject *py_basicsize;
    py_basicsize = PyObject_GetAttrString(cached_type, "__basicsize__");
    if (unlikely(!py_basicsize)) return -1;
    basicsize = PyLong_AsSsize_t(py_basicsize);
    Py_DECREF(py_basicsize);
    py_basicsize = NULL;
    if (unlikely(basicsize == (Py_ssize_t)-1) && PyErr_Occurred()) return -1;
#else
    basicsize = ((PyTypeObject*) cached_type)->tp_basicsize;
#endif
    if (basicsize != expected_basicsize) {
        PyErr_Format(PyExc_TypeError,
            "Shared Cython type %.200s has the wrong size, try recompiling",
            name);
        return -1;
    }
    return 0;
}
static PyTypeObject *__Pyx_FetchCommonTypeFromSpec(PyTypeObject *metaclass, PyObject *module, PyType_Spec *spec, PyObject *bases) {
    PyObject *abi_module = NULL, *cached_type = NULL, *abi_module_dict, *new_cached_type, *py_object_name;
    int get_item_ref_result;
    const char* object_name = strrchr(spec->name, '.');
    object_name = object_name ? object_name+1 : spec->name;
    py_object_name = PyUnicode_FromString(object_name);
    if (!py_object_name) return NULL;
    abi_module = __Pyx_FetchSharedCythonABIModule();
    if (!abi_module) goto done;
    abi_module_dict = PyModule_GetDict(abi_module);
    if (!abi_module_dict) goto done;
    get_item_ref_result = __Pyx_PyDict_GetItemRef(abi_module_dict, py_object_name, &cached_type);
    if (get_item_ref_result == 1) {
        if (__Pyx_VerifyCachedType(
              cached_type,
              object_name,
              spec->basicsize) < 0) {
            goto bad;
        }
        goto done;
    } else if (unlikely(get_item_ref_result == -1)) {
        goto bad;
    }
    CYTHON_UNUSED_VAR(module);
    cached_type = __Pyx_PyType_FromMetaclass(metaclass, abi_module, spec, bases);
    if (unlikely(!cached_type)) goto bad;
    if (unlikely(__Pyx_fix_up_extension_type_from_spec(spec, (PyTypeObject *) cached_type) < 0)) goto bad;
    new_cached_type = __Pyx_PyDict_SetDefault(abi_module_dict, py_object_name, cached_type, 1);
    if (unlikely(new_cached_type != cached_type)) {
        if (unlikely(!new_cached_type)) goto bad;
        Py_DECREF(cached_type);
        cached_type = new_cached_type;
        if (__Pyx_VerifyCachedType(
                cached_type,
                object_name,
                spec->basicsize) < 0) {
            goto bad;
        }
        goto done;
    } else {
        Py_DECREF(new_cached_type);
    }
done:
    Py_XDECREF(abi_module);
    Py_DECREF(py_object_name);
    assert(cached_type == NULL || PyType_Check(cached_type));
    return (PyTypeObject *) cached_type;
bad:
    Py_XDECREF(cached_type);
    cached_type = NULL;
    goto done;
}

/* CommonTypesMetaclass */
PyObject* __pyx_CommonTypesMetaclass_get_module(CYTHON_UNUSED PyObject *self, CYTHON_UNUSED void* context) {
    return PyUnicode_FromString(__PYX_ABI_MODULE_NAME);
}
static PyGetSetDef __pyx_CommonTypesMetaclass_getset[] = {
    {"__module__", __pyx_CommonTypesMetaclass_get_module, NULL, NULL, NULL},
    {0, 0, 0, 0, 0}
};
static PyType_Slot __pyx_CommonTypesMetaclass_slots[] = {
    {Py_tp_getset, (void *)__pyx_CommonTypesMetaclass_getset},
    {0, 0}
};
static PyType_Spec __pyx_CommonTypesMetaclass_spec = {
    __PYX_TYPE_MODULE_PREFIX "_common_types_metatype",
    0,
    0,
#if PY_VERSION_HEX >= 0x030A0000
    Py_TPFLAGS_IMMUTABLETYPE |
    Py_TPFLAGS_DISALLOW_INSTANTIATION |
#endif
    Py_TPFLAGS_DEFAULT,
    __pyx_CommonTypesMetaclass_slots
};
static int __pyx_CommonTypesMetaclass_init(PyObject *module) {
    __pyx_mstatetype *mstate = __Pyx_PyModule_GetState(module);
    PyObject *bases = PyTuple_Pack(1, &PyType_Type);
    if (unlikely(!bases)) {
        return -1;
    }
    mstate->__pyx_CommonTypesMetaclassType = __Pyx_FetchCommonTypeFromSpec(NULL, module, &__pyx_CommonTypesMetaclass_spec, bases);
    if (unlikely(mstate->__pyx_CommonTypesMetaclassType == NULL)) {
        return -1;
    }
    return 0;
}

/* CallTypeTraverse */
#if !CYTHON_USE_TYPE_SPECS || (!CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX < 0x03090000)
#else
static int __Pyx_call_type_traverse(PyObject *o, int always_call, visitproc visit, void *arg) {
    #if CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX < 0x03090000
    if (__Pyx_get_runtime_version() < 0x03090000) return 0;
    #endif
    if (!always_call) {
        PyTypeObject *base = __Pyx_PyObject_GetSlot(o, tp_base, PyTypeObject*);
        unsigned long flags = PyType_GetFlags(base);
        if (flags & Py_TPFLAGS_HEAPTYPE) {
            return 0;
        }
    }
    Py_VISIT((PyObject*)Py_TYPE(o));
    return 0;
}
#endif

/* PyMethodNew */
#if CYTHON_COMPILING_IN_LIMITED_API
static PyObject *__Pyx_PyMethod_New(PyObject *func, PyObject *self, PyObject *typ) {
    PyObject *result;
    CYTHON_UNUSED_VAR(typ);
    if (!self)
        return __Pyx_NewRef(func);
    #if __PYX_LIMITED_VERSION_HEX >= 0x030C0000
    {
        PyObject *args[] = {func, self};
        result = PyObject_Vectorcall(__pyx_mstate_global->__Pyx_CachedMethodType, args, 2, NULL);
    }
    #else
    result = PyObject_CallFunctionObjArgs(__pyx_mstate_global->__Pyx_CachedMethodType, func, self, NULL);
    #endif
    return result;
}
#else
static PyObject *__Pyx_PyMethod_New(PyObject *func, PyObject *self, PyObject *typ) {
    CYTHON_UNUSED_VAR(typ);
    if (!self)
        return __Pyx_NewRef(func);
    return PyMethod_New(func, self);
}
#endif

/* PyVectorcallFastCallDict */
#if CYTHON_METH_FASTCALL && (CYTHON_VECTORCALL || CYTHON_BACKPORT_VECTORCALL)
static PyObject *__Pyx_PyVectorcall_FastCallDict_kw(PyObject *func, __pyx_vectorcallfunc vc, PyObject *const *args, size_t nargs, PyObject *kw)
{
    PyObject *res = NULL;
    PyObject *kwnames;
    PyObject **newargs;
    PyObject **kwvalues;
    Py_ssize_t i, pos;
    size_t j;
    PyObject *key, *value;
    unsigned long keys_are_strings;
    #if !CYTHON_ASSUME_SAFE_SIZE
    Py_ssize_t nkw = PyDict_Size(kw);
    if (unlikely(nkw == -1)) return NULL;
    #else
    Py_ssize_t nkw = PyDict_GET_SIZE(kw);
    #endif
    newargs = (PyObject **)PyMem_Malloc((nargs + (size_t)nkw) * sizeof(args[0]));
    if (unlikely(newargs == NULL)) {
        PyErr_NoMemory();
        return NULL;
    }
    for (j = 0; j < nargs; j++) newargs[j] = args[j];
    kwnames = PyTuple_New(nkw);
    if (unlikely(kwnames == NULL)) {
        PyMem_Free(newargs);
        return NULL;
    }
    kwvalues = newargs + nargs;
    pos = i = 0;
    keys_are_strings = Py_TPFLAGS_UNICODE_SUBCLASS;
    while (PyDict_Next(kw, &pos, &key, &value)) {
        keys_are_strings &=
        #if CYTHON_COMPILING_IN_LIMITED_API
            PyType_GetFlags(Py_TYPE(key));
        #else
            Py_TYPE(key)->tp_flags;
        #endif
        Py_INCREF(key);
        Py_INCREF(value);
        #if !CYTHON_ASSUME_SAFE_MACROS
        if (unlikely(PyTuple_SetItem(kwnames, i, key) < 0)) goto cleanup;
        #else
        PyTuple_SET_ITEM(kwnames, i, key);
        #endif
        kwvalues[i] = value;
        i++;
    }
    if (unlikely(!keys_are_strings)) {
        PyErr_SetString(PyExc_TypeError, "keywords must be strings");
        goto cleanup;
    }
    res = vc(func, newargs, nargs, kwnames);
cleanup:
    Py_DECREF(kwnames);
    for (i = 0; i < nkw; i++)
        Py_DECREF(kwvalues[i]);
    PyMem_Free(newargs);
    return res;
}
static CYTHON_INLINE PyObject *__Pyx_PyVectorcall_FastCallDict(PyObject *func, __pyx_vectorcallfunc vc, PyObject *const *args, size_t nargs, PyObject *kw)
{
    Py_ssize_t kw_size =
        likely(kw == NULL) ?
        0 :
#if !CYTHON_ASSUME_SAFE_SIZE
        PyDict_Size(kw);
#else
        PyDict_GET_SIZE(kw);
#endif
    if (kw_size == 0) {
        return vc(func, args, nargs, NULL);
    }
#if !CYTHON_ASSUME_SAFE_SIZE
    else if (unlikely(kw_size == -1)) {
        return NULL;
    }
#endif
    return __Pyx_PyVectorcall_FastCallDict_kw(func, vc, args, nargs, kw);
}
#endif

/* CythonFunctionShared */
#if CYTHON_COMPILING_IN_LIMITED_API
static CYTHON_INLINE int __Pyx__IsSameCyOrCFunctionNoMethod(PyObject *func, void (*cfunc)(void)) {
    if (__Pyx_CyFunction_Check(func)) {
        return PyCFunction_GetFunction(((__pyx_CyFunctionObject*)func)->func) == (PyCFunction) cfunc;
    } else if (PyCFunction_Check(func)) {
        return PyCFunction_GetFunction(func) == (PyCFunction) cfunc;
    }
    return 0;
}
static CYTHON_INLINE int __Pyx__IsSameCyOrCFunction(PyObject *func, void (*cfunc)(void)) {
    if ((PyObject*)Py_TYPE(func) == __pyx_mstate_global->__Pyx_CachedMethodType) {
        int result;
        PyObject *newFunc = PyObject_GetAttr(func, __pyx_mstate_global->__pyx_n_u_func);
        if (unlikely(!newFunc)) {
            PyErr_Clear(); // It's only an optimization, so don't throw an error
            return 0;
        }
        result = __Pyx__IsSameCyOrCFunctionNoMethod(newFunc, cfunc);
        Py_DECREF(newFunc);
        return result;
    }
    return __Pyx__IsSameCyOrCFunctionNoMethod(func, cfunc);
}
#else
static CYTHON_INLINE int __Pyx__IsSameCyOrCFunction(PyObject *func, void (*cfunc)(void)) {
    if (PyMethod_Check(func)) {
        func = PyMethod_GET_FUNCTION(func);
    }
    return __Pyx_CyOrPyCFunction_Check(func) && __Pyx_CyOrPyCFunction_GET_FUNCTION(func) == (PyCFunction) cfunc;
}
#endif
static CYTHON_INLINE void __Pyx__CyFunction_SetClassObj(__pyx_CyFunctionObject* f, PyObject* classobj) {
#if PY_VERSION_HEX < 0x030900B1 || CYTHON_COMPILING_IN_LIMITED_API
    __Pyx_Py_XDECREF_SET(
        __Pyx_CyFunction_GetClassObj(f),
            ((classobj) ? __Pyx_NewRef(classobj) : NULL));
#else
    __Pyx_Py_XDECREF_SET(
        ((PyCMethodObject *) (f))->mm_class,
        (PyTypeObject*)((classobj) ? __Pyx_NewRef(classobj) : NULL));
#endif
}
static PyObject *
__Pyx_CyFunction_get_doc_locked(__pyx_CyFunctionObject *op)
{
    if (unlikely(op->func_doc == NULL)) {
#if CYTHON_COMPILING_IN_LIMITED_API
        op->func_doc = PyObject_GetAttrString(op->func, "__doc__");
        if (unlikely(!op->func_doc)) return NULL;
#else
        if (((PyCFunctionObject*)op)->m_ml->ml_doc) {
            op->func_doc = PyUnicode_FromString(((PyCFunctionObject*)op)->m_ml->ml_doc);
            if (unlikely(op->func_doc == NULL))
                return NULL;
        } else {
            Py_INCREF(Py_None);
            return Py_None;
        }
#endif
    }
    Py_INCREF(op->func_doc);
    return op->func_doc;
}
static PyObject *
__Pyx_CyFunction_get_doc(__pyx_CyFunctionObject *op, void *closure) {
    PyObject *result;
    CYTHON_UNUSED_VAR(closure);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_doc_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_doc(__pyx_CyFunctionObject *op, PyObject *value, void *context)
{
    CYTHON_UNUSED_VAR(context);
    if (value == NULL) {
        value = Py_None;
    }
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->func_doc, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_name_locked(__pyx_CyFunctionObject *op)
{
    if (unlikely(op->func_name == NULL)) {
#if CYTHON_COMPILING_IN_LIMITED_API
        op->func_name = PyObject_GetAttrString(op->func, "__name__");
#else
        op->func_name = PyUnicode_InternFromString(((PyCFunctionObject*)op)->m_ml->ml_name);
#endif
        if (unlikely(op->func_name == NULL))
            return NULL;
    }
    Py_INCREF(op->func_name);
    return op->func_name;
}
static PyObject *
__Pyx_CyFunction_get_name(__pyx_CyFunctionObject *op, void *context)
{
    PyObject *result = NULL;
    CYTHON_UNUSED_VAR(context);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_name_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_name(__pyx_CyFunctionObject *op, PyObject *value, void *context)
{
    CYTHON_UNUSED_VAR(context);
    if (unlikely(value == NULL || !PyUnicode_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
                        "__name__ must be set to a string object");
        return -1;
    }
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->func_name, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_qualname(__pyx_CyFunctionObject *op, void *context)
{
    CYTHON_UNUSED_VAR(context);
    PyObject *result;
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    Py_INCREF(op->func_qualname);
    result = op->func_qualname;
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_qualname(__pyx_CyFunctionObject *op, PyObject *value, void *context)
{
    CYTHON_UNUSED_VAR(context);
    if (unlikely(value == NULL || !PyUnicode_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
                        "__qualname__ must be set to a string object");
        return -1;
    }
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->func_qualname, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_dict_locked(__pyx_CyFunctionObject *op)
{
    if (unlikely(op->func_dict == NULL)) {
        op->func_dict = PyDict_New();
        if (unlikely(op->func_dict == NULL))
            return NULL;
    }
    Py_INCREF(op->func_dict);
    return op->func_dict;
}
static PyObject *
__Pyx_CyFunction_get_dict(__pyx_CyFunctionObject *op, void *context)
{
    CYTHON_UNUSED_VAR(context);
    PyObject *result;
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_dict_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_dict(__pyx_CyFunctionObject *op, PyObject *value, void *context)
{
    CYTHON_UNUSED_VAR(context);
    if (unlikely(value == NULL)) {
        PyErr_SetString(PyExc_TypeError,
               "function's dictionary may not be deleted");
        return -1;
    }
    if (unlikely(!PyDict_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
               "setting function's dictionary to a non-dict");
        return -1;
    }
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->func_dict, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_globals(__pyx_CyFunctionObject *op, void *context)
{
    CYTHON_UNUSED_VAR(context);
    Py_INCREF(op->func_globals);
    return op->func_globals;
}
static PyObject *
__Pyx_CyFunction_get_closure(__pyx_CyFunctionObject *op, void *context)
{
    CYTHON_UNUSED_VAR(op);
    CYTHON_UNUSED_VAR(context);
    Py_INCREF(Py_None);
    return Py_None;
}
static PyObject *
__Pyx_CyFunction_get_code(__pyx_CyFunctionObject *op, void *context)
{
    PyObject* result = (op->func_code) ? op->func_code : Py_None;
    CYTHON_UNUSED_VAR(context);
    Py_INCREF(result);
    return result;
}
static int
__Pyx_CyFunction_init_defaults(__pyx_CyFunctionObject *op) {
    int result = 0;
    PyObject *res = op->defaults_getter((PyObject *) op);
    if (unlikely(!res))
        return -1;
    #if CYTHON_ASSUME_SAFE_MACROS && !CYTHON_AVOID_BORROWED_REFS
    op->defaults_tuple = PyTuple_GET_ITEM(res, 0);
    Py_INCREF(op->defaults_tuple);
    op->defaults_kwdict = PyTuple_GET_ITEM(res, 1);
    Py_INCREF(op->defaults_kwdict);
    #else
    op->defaults_tuple = __Pyx_PySequence_ITEM(res, 0);
    if (unlikely(!op->defaults_tuple)) result = -1;
    else {
        op->defaults_kwdict = __Pyx_PySequence_ITEM(res, 1);
        if (unlikely(!op->defaults_kwdict)) result = -1;
    }
    #endif
    Py_DECREF(res);
    return result;
}
static int
__Pyx_CyFunction_set_defaults(__pyx_CyFunctionObject *op, PyObject* value, void *context) {
    CYTHON_UNUSED_VAR(context);
    if (!value) {
        value = Py_None;
    } else if (unlikely(value != Py_None && !PyTuple_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
                        "__defaults__ must be set to a tuple object");
        return -1;
    }
    PyErr_WarnEx(PyExc_RuntimeWarning, "changes to cyfunction.__defaults__ will not "
                 "currently affect the values used in function calls", 1);
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->defaults_tuple, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_defaults_locked(__pyx_CyFunctionObject *op) {
    PyObject* result = op->defaults_tuple;
    if (unlikely(!result)) {
        if (op->defaults_getter) {
            if (unlikely(__Pyx_CyFunction_init_defaults(op) < 0)) return NULL;
            result = op->defaults_tuple;
        } else {
            result = Py_None;
        }
    }
    Py_INCREF(result);
    return result;
}
static PyObject *
__Pyx_CyFunction_get_defaults(__pyx_CyFunctionObject *op, void *context) {
    PyObject* result = NULL;
    CYTHON_UNUSED_VAR(context);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_defaults_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_kwdefaults(__pyx_CyFunctionObject *op, PyObject* value, void *context) {
    CYTHON_UNUSED_VAR(context);
    if (!value) {
        value = Py_None;
    } else if (unlikely(value != Py_None && !PyDict_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
                        "__kwdefaults__ must be set to a dict object");
        return -1;
    }
    PyErr_WarnEx(PyExc_RuntimeWarning, "changes to cyfunction.__kwdefaults__ will not "
                 "currently affect the values used in function calls", 1);
    Py_INCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->defaults_kwdict, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_kwdefaults_locked(__pyx_CyFunctionObject *op) {
    PyObject* result = op->defaults_kwdict;
    if (unlikely(!result)) {
        if (op->defaults_getter) {
            if (unlikely(__Pyx_CyFunction_init_defaults(op) < 0)) return NULL;
            result = op->defaults_kwdict;
        } else {
            result = Py_None;
        }
    }
    Py_INCREF(result);
    return result;
}
static PyObject *
__Pyx_CyFunction_get_kwdefaults(__pyx_CyFunctionObject *op, void *context) {
    PyObject* result;
    CYTHON_UNUSED_VAR(context);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_kwdefaults_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static int
__Pyx_CyFunction_set_annotations(__pyx_CyFunctionObject *op, PyObject* value, void *context) {
    CYTHON_UNUSED_VAR(context);
    if (!value || value == Py_None) {
        value = NULL;
    } else if (unlikely(!PyDict_Check(value))) {
        PyErr_SetString(PyExc_TypeError,
                        "__annotations__ must be set to a dict object");
        return -1;
    }
    Py_XINCREF(value);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    __Pyx_Py_XDECREF_SET(op->func_annotations, value);
    __Pyx_END_CRITICAL_SECTION();
    return 0;
}
static PyObject *
__Pyx_CyFunction_get_annotations_locked(__pyx_CyFunctionObject *op) {
    PyObject* result = op->func_annotations;
    if (unlikely(!result)) {
        result = PyDict_New();
        if (unlikely(!result)) return NULL;
        op->func_annotations = result;
    }
    Py_INCREF(result);
    return result;
}
static PyObject *
__Pyx_CyFunction_get_annotations(__pyx_CyFunctionObject *op, void *context) {
    PyObject *result;
    CYTHON_UNUSED_VAR(context);
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    result = __Pyx_CyFunction_get_annotations_locked(op);
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static PyObject *
__Pyx_CyFunction_get_is_coroutine_value(__pyx_CyFunctionObject *op) {
    int is_coroutine = op->flags & __Pyx_CYFUNCTION_COROUTINE;
    if (is_coroutine) {
        PyObject *is_coroutine_value, *module, *fromlist, *marker = __pyx_mstate_global->__pyx_n_u_is_coroutine;
        fromlist = PyList_New(1);
        if (unlikely(!fromlist)) return NULL;
        Py_INCREF(marker);
#if CYTHON_ASSUME_SAFE_MACROS
        PyList_SET_ITEM(fromlist, 0, marker);
#else
        if (unlikely(PyList_SetItem(fromlist, 0, marker) < 0)) {
            Py_DECREF(marker);
            Py_DECREF(fromlist);
            return NULL;
        }
#endif
        module = PyImport_ImportModuleLevelObject(__pyx_mstate_global->__pyx_n_u_asyncio_coroutines, NULL, NULL, fromlist, 0);
        Py_DECREF(fromlist);
        if (unlikely(!module)) goto ignore;
        is_coroutine_value = __Pyx_PyObject_GetAttrStr(module, marker);
        Py_DECREF(module);
        if (likely(is_coroutine_value)) {
            return is_coroutine_value;
        }
ignore:
        PyErr_Clear();
    }
    return __Pyx_PyBool_FromLong(is_coroutine);
}
static PyObject *
__Pyx_CyFunction_get_is_coroutine(__pyx_CyFunctionObject *op, void *context) {
    PyObject *result;
    CYTHON_UNUSED_VAR(context);
    if (op->func_is_coroutine) {
        return __Pyx_NewRef(op->func_is_coroutine);
    }
    result = __Pyx_CyFunction_get_is_coroutine_value(op);
    if (unlikely(!result))
        return NULL;
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    if (op->func_is_coroutine) {
        Py_DECREF(result);
        result = __Pyx_NewRef(op->func_is_coroutine);
    } else {
        op->func_is_coroutine = __Pyx_NewRef(result);
    }
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static void __Pyx_CyFunction_raise_argument_count_error(__pyx_CyFunctionObject *func, const char* message, Py_ssize_t size) {
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject *py_name = __Pyx_CyFunction_get_name(func, NULL);
    if (!py_name) return;
    PyErr_Format(PyExc_TypeError,
        "%.200S() %s (%" CYTHON_FORMAT_SSIZE_T "d given)",
        py_name, message, size);
    Py_DECREF(py_name);
#else
    const char* name = ((PyCFunctionObject*)func)->m_ml->ml_name;
    PyErr_Format(PyExc_TypeError,
        "%.200s() %s (%" CYTHON_FORMAT_SSIZE_T "d given)",
        name, message, size);
#endif
}
static void __Pyx_CyFunction_raise_type_error(__pyx_CyFunctionObject *func, const char* message) {
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject *py_name = __Pyx_CyFunction_get_name(func, NULL);
    if (!py_name) return;
    PyErr_Format(PyExc_TypeError,
        "%.200S() %s",
        py_name, message);
    Py_DECREF(py_name);
#else
    const char* name = ((PyCFunctionObject*)func)->m_ml->ml_name;
    PyErr_Format(PyExc_TypeError,
        "%.200s() %s",
        name, message);
#endif
}
#if CYTHON_COMPILING_IN_LIMITED_API
static PyObject *
__Pyx_CyFunction_get_module(__pyx_CyFunctionObject *op, void *context) {
    CYTHON_UNUSED_VAR(context);
    return PyObject_GetAttrString(op->func, "__module__");
}
static int
__Pyx_CyFunction_set_module(__pyx_CyFunctionObject *op, PyObject* value, void *context) {
    CYTHON_UNUSED_VAR(context);
    return PyObject_SetAttrString(op->func, "__module__", value);
}
#endif
static PyGetSetDef __pyx_CyFunction_getsets[] = {
    {"func_doc", (getter)__Pyx_CyFunction_get_doc, (setter)__Pyx_CyFunction_set_doc, 0, 0},
    {"__doc__",  (getter)__Pyx_CyFunction_get_doc, (setter)__Pyx_CyFunction_set_doc, 0, 0},
    {"func_name", (getter)__Pyx_CyFunction_get_name, (setter)__Pyx_CyFunction_set_name, 0, 0},
    {"__name__", (getter)__Pyx_CyFunction_get_name, (setter)__Pyx_CyFunction_set_name, 0, 0},
    {"__qualname__", (getter)__Pyx_CyFunction_get_qualname, (setter)__Pyx_CyFunction_set_qualname, 0, 0},
    {"func_dict", (getter)__Pyx_CyFunction_get_dict, (setter)__Pyx_CyFunction_set_dict, 0, 0},
    {"__dict__", (getter)__Pyx_CyFunction_get_dict, (setter)__Pyx_CyFunction_set_dict, 0, 0},
    {"func_globals", (getter)__Pyx_CyFunction_get_globals, 0, 0, 0},
    {"__globals__", (getter)__Pyx_CyFunction_get_globals, 0, 0, 0},
    {"func_closure", (getter)__Pyx_CyFunction_get_closure, 0, 0, 0},
    {"__closure__", (getter)__Pyx_CyFunction_get_closure, 0, 0, 0},
    {"func_code", (getter)__Pyx_CyFunction_get_code, 0, 0, 0},
    {"__code__", (getter)__Pyx_CyFunction_get_code, 0, 0, 0},
    {"func_defaults", (getter)__Pyx_CyFunction_get_defaults, (setter)__Pyx_CyFunction_set_defaults, 0, 0},
    {"__defaults__", (getter)__Pyx_CyFunction_get_defaults, (setter)__Pyx_CyFunction_set_defaults, 0, 0},
    {"__kwdefaults__", (getter)__Pyx_CyFunction_get_kwdefaults, (setter)__Pyx_CyFunction_set_kwdefaults, 0, 0},
    {"__annotations__", (getter)__Pyx_CyFunction_get_annotations, (setter)__Pyx_CyFunction_set_annotations, 0, 0},
    {"_is_coroutine", (getter)__Pyx_CyFunction_get_is_coroutine, 0, 0, 0},
#if CYTHON_COMPILING_IN_LIMITED_API
    {"__module__", (getter)__Pyx_CyFunction_get_module, (setter)__Pyx_CyFunction_set_module, 0, 0},
#endif
    {0, 0, 0, 0, 0}
};
static PyMemberDef __pyx_CyFunction_members[] = {
#if !CYTHON_COMPILING_IN_LIMITED_API
    {"__module__", T_OBJECT, offsetof(PyCFunctionObject, m_module), 0, 0},
#endif
    {"__dictoffset__", T_PYSSIZET, offsetof(__pyx_CyFunctionObject, func_dict), READONLY, 0},
#if CYTHON_METH_FASTCALL
#if CYTHON_BACKPORT_VECTORCALL || CYTHON_COMPILING_IN_LIMITED_API
    {"__vectorcalloffset__", T_PYSSIZET, offsetof(__pyx_CyFunctionObject, func_vectorcall), READONLY, 0},
#else
    {"__vectorcalloffset__", T_PYSSIZET, offsetof(PyCFunctionObject, vectorcall), READONLY, 0},
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
    {"__weaklistoffset__", T_PYSSIZET, offsetof(__pyx_CyFunctionObject, func_weakreflist), READONLY, 0},
#else
    {"__weaklistoffset__", T_PYSSIZET, offsetof(PyCFunctionObject, m_weakreflist), READONLY, 0},
#endif
#endif
    {0, 0, 0,  0, 0}
};
static PyObject *
__Pyx_CyFunction_reduce(__pyx_CyFunctionObject *m, PyObject *args)
{
    PyObject *result = NULL;
    CYTHON_UNUSED_VAR(args);
    __Pyx_BEGIN_CRITICAL_SECTION(m);
    Py_INCREF(m->func_qualname);
    result = m->func_qualname;
    __Pyx_END_CRITICAL_SECTION();
    return result;
}
static PyMethodDef __pyx_CyFunction_methods[] = {
    {"__reduce__", (PyCFunction)__Pyx_CyFunction_reduce, METH_VARARGS, 0},
    {0, 0, 0, 0}
};
#if CYTHON_COMPILING_IN_LIMITED_API
#define __Pyx_CyFunction_weakreflist(cyfunc) ((cyfunc)->func_weakreflist)
#else
#define __Pyx_CyFunction_weakreflist(cyfunc) (((PyCFunctionObject*)cyfunc)->m_weakreflist)
#endif
static PyObject *__Pyx_CyFunction_Init(__pyx_CyFunctionObject *op, PyMethodDef *ml, int flags, PyObject* qualname,
                                       PyObject *closure, PyObject *module, PyObject* globals, PyObject* code) {
#if !CYTHON_COMPILING_IN_LIMITED_API
    PyCFunctionObject *cf = (PyCFunctionObject*) op;
#endif
    if (unlikely(op == NULL))
        return NULL;
#if CYTHON_COMPILING_IN_LIMITED_API
    op->func = PyCFunction_NewEx(ml, (PyObject*)op, module);
    if (unlikely(!op->func)) return NULL;
#endif
    op->flags = flags;
    __Pyx_CyFunction_weakreflist(op) = NULL;
#if !CYTHON_COMPILING_IN_LIMITED_API
    cf->m_ml = ml;
    cf->m_self = (PyObject *) op;
#endif
    Py_XINCREF(closure);
    op->func_closure = closure;
#if !CYTHON_COMPILING_IN_LIMITED_API
    Py_XINCREF(module);
    cf->m_module = module;
#endif
    op->func_dict = NULL;
    op->func_name = NULL;
    Py_INCREF(qualname);
    op->func_qualname = qualname;
    op->func_doc = NULL;
#if PY_VERSION_HEX < 0x030900B1 || CYTHON_COMPILING_IN_LIMITED_API
    op->func_classobj = NULL;
#else
    ((PyCMethodObject*)op)->mm_class = NULL;
#endif
    op->func_globals = globals;
    Py_INCREF(op->func_globals);
    Py_XINCREF(code);
    op->func_code = code;
    op->defaults = NULL;
    op->defaults_tuple = NULL;
    op->defaults_kwdict = NULL;
    op->defaults_getter = NULL;
    op->func_annotations = NULL;
    op->func_is_coroutine = NULL;
#if CYTHON_METH_FASTCALL
    switch (ml->ml_flags & (METH_VARARGS | METH_FASTCALL | METH_NOARGS | METH_O | METH_KEYWORDS | METH_METHOD)) {
    case METH_NOARGS:
        __Pyx_CyFunction_func_vectorcall(op) = __Pyx_CyFunction_Vectorcall_NOARGS;
        break;
    case METH_O:
        __Pyx_CyFunction_func_vectorcall(op) = __Pyx_CyFunction_Vectorcall_O;
        break;
    case METH_METHOD | METH_FASTCALL | METH_KEYWORDS:
        __Pyx_CyFunction_func_vectorcall(op) = __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS_METHOD;
        break;
    case METH_FASTCALL | METH_KEYWORDS:
        __Pyx_CyFunction_func_vectorcall(op) = __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS;
        break;
    case METH_VARARGS | METH_KEYWORDS:
        __Pyx_CyFunction_func_vectorcall(op) = NULL;
        break;
    default:
        PyErr_SetString(PyExc_SystemError, "Bad call flags for CyFunction");
        Py_DECREF(op);
        return NULL;
    }
#endif
    return (PyObject *) op;
}
static int
__Pyx_CyFunction_clear(__pyx_CyFunctionObject *m)
{
    Py_CLEAR(m->func_closure);
#if CYTHON_COMPILING_IN_LIMITED_API
    Py_CLEAR(m->func);
#else
    Py_CLEAR(((PyCFunctionObject*)m)->m_module);
#endif
    Py_CLEAR(m->func_dict);
    Py_CLEAR(m->func_name);
    Py_CLEAR(m->func_qualname);
    Py_CLEAR(m->func_doc);
    Py_CLEAR(m->func_globals);
    Py_CLEAR(m->func_code);
#if !CYTHON_COMPILING_IN_LIMITED_API
#if PY_VERSION_HEX < 0x030900B1
    Py_CLEAR(__Pyx_CyFunction_GetClassObj(m));
#else
    {
        PyObject *cls = (PyObject*) ((PyCMethodObject *) (m))->mm_class;
        ((PyCMethodObject *) (m))->mm_class = NULL;
        Py_XDECREF(cls);
    }
#endif
#endif
    Py_CLEAR(m->defaults_tuple);
    Py_CLEAR(m->defaults_kwdict);
    Py_CLEAR(m->func_annotations);
    Py_CLEAR(m->func_is_coroutine);
    Py_CLEAR(m->defaults);
    return 0;
}
static void __Pyx__CyFunction_dealloc(__pyx_CyFunctionObject *m)
{
    if (__Pyx_CyFunction_weakreflist(m) != NULL)
        PyObject_ClearWeakRefs((PyObject *) m);
    __Pyx_CyFunction_clear(m);
    __Pyx_PyHeapTypeObject_GC_Del(m);
}
static void __Pyx_CyFunction_dealloc(__pyx_CyFunctionObject *m)
{
    PyObject_GC_UnTrack(m);
    __Pyx__CyFunction_dealloc(m);
}
static int __Pyx_CyFunction_traverse(__pyx_CyFunctionObject *m, visitproc visit, void *arg)
{
    {
        int e = __Pyx_call_type_traverse((PyObject*)m, 1, visit, arg);
        if (e) return e;
    }
    Py_VISIT(m->func_closure);
#if CYTHON_COMPILING_IN_LIMITED_API
    Py_VISIT(m->func);
#else
    Py_VISIT(((PyCFunctionObject*)m)->m_module);
#endif
    Py_VISIT(m->func_dict);
    __Pyx_VISIT_CONST(m->func_name);
    __Pyx_VISIT_CONST(m->func_qualname);
    Py_VISIT(m->func_doc);
    Py_VISIT(m->func_globals);
    __Pyx_VISIT_CONST(m->func_code);
#if !CYTHON_COMPILING_IN_LIMITED_API
    Py_VISIT(__Pyx_CyFunction_GetClassObj(m));
#endif
    Py_VISIT(m->defaults_tuple);
    Py_VISIT(m->defaults_kwdict);
    Py_VISIT(m->func_is_coroutine);
    Py_VISIT(m->defaults);
    return 0;
}
static PyObject*
__Pyx_CyFunction_repr(__pyx_CyFunctionObject *op)
{
    PyObject *repr;
    __Pyx_BEGIN_CRITICAL_SECTION(op);
    repr = PyUnicode_FromFormat("<cyfunction %U at %p>",
                                op->func_qualname, (void *)op);
    __Pyx_END_CRITICAL_SECTION();
    return repr;
}
static PyObject * __Pyx_CyFunction_CallMethod(PyObject *func, PyObject *self, PyObject *arg, PyObject *kw) {
#if CYTHON_COMPILING_IN_LIMITED_API
    PyObject *f = ((__pyx_CyFunctionObject*)func)->func;
    PyCFunction meth;
    int flags;
    meth = PyCFunction_GetFunction(f);
    if (unlikely(!meth)) return NULL;
    flags = PyCFunction_GetFlags(f);
    if (unlikely(flags < 0)) return NULL;
#else
    PyCFunctionObject* f = (PyCFunctionObject*)func;
    PyCFunction meth = f->m_ml->ml_meth;
    int flags = f->m_ml->ml_flags;
#endif
    Py_ssize_t size;
    switch (flags & (METH_VARARGS | METH_KEYWORDS | METH_NOARGS | METH_O)) {
    case METH_VARARGS:
        if (likely(kw == NULL || PyDict_Size(kw) == 0))
            return (*meth)(self, arg);
        break;
    case METH_VARARGS | METH_KEYWORDS:
        return (*(PyCFunctionWithKeywords)(void(*)(void))meth)(self, arg, kw);
    case METH_NOARGS:
        if (likely(kw == NULL || PyDict_Size(kw) == 0)) {
#if CYTHON_ASSUME_SAFE_SIZE
            size = PyTuple_GET_SIZE(arg);
#else
            size = PyTuple_Size(arg);
            if (unlikely(size < 0)) return NULL;
#endif
            if (likely(size == 0))
                return (*meth)(self, NULL);
            __Pyx_CyFunction_raise_argument_count_error(
                (__pyx_CyFunctionObject*)func,
                "takes no arguments", size);
            return NULL;
        }
        break;
    case METH_O:
        if (likely(kw == NULL || PyDict_Size(kw) == 0)) {
#if CYTHON_ASSUME_SAFE_SIZE
            size = PyTuple_GET_SIZE(arg);
#else
            size = PyTuple_Size(arg);
            if (unlikely(size < 0)) return NULL;
#endif
            if (likely(size == 1)) {
                PyObject *result, *arg0;
                #if CYTHON_ASSUME_SAFE_MACROS && !CYTHON_AVOID_BORROWED_REFS
                arg0 = PyTuple_GET_ITEM(arg, 0);
                #else
                arg0 = __Pyx_PySequence_ITEM(arg, 0); if (unlikely(!arg0)) return NULL;
                #endif
                result = (*meth)(self, arg0);
                #if !(CYTHON_ASSUME_SAFE_MACROS && !CYTHON_AVOID_BORROWED_REFS)
                Py_DECREF(arg0);
                #endif
                return result;
            }
            __Pyx_CyFunction_raise_argument_count_error(
                (__pyx_CyFunctionObject*)func,
                "takes exactly one argument", size);
            return NULL;
        }
        break;
    default:
        PyErr_SetString(PyExc_SystemError, "Bad call flags for CyFunction");
        return NULL;
    }
    __Pyx_CyFunction_raise_type_error(
        (__pyx_CyFunctionObject*)func, "takes no keyword arguments");
    return NULL;
}
static CYTHON_INLINE PyObject *__Pyx_CyFunction_Call(PyObject *func, PyObject *arg, PyObject *kw) {
    PyObject *self, *result;
#if CYTHON_COMPILING_IN_LIMITED_API
    self = PyCFunction_GetSelf(((__pyx_CyFunctionObject*)func)->func);
    if (unlikely(!self) && PyErr_Occurred()) return NULL;
#else
    self = ((PyCFunctionObject*)func)->m_self;
#endif
    result = __Pyx_CyFunction_CallMethod(func, self, arg, kw);
    return result;
}
static PyObject *__Pyx_CyFunction_CallAsMethod(PyObject *func, PyObject *args, PyObject *kw) {
    PyObject *result;
    __pyx_CyFunctionObject *cyfunc = (__pyx_CyFunctionObject *) func;
#if CYTHON_METH_FASTCALL && (CYTHON_VECTORCALL || CYTHON_BACKPORT_VECTORCALL)
     __pyx_vectorcallfunc vc = __Pyx_CyFunction_func_vectorcall(cyfunc);
    if (vc) {
#if CYTHON_ASSUME_SAFE_MACROS && CYTHON_ASSUME_SAFE_SIZE
        return __Pyx_PyVectorcall_FastCallDict(func, vc, &PyTuple_GET_ITEM(args, 0), (size_t)PyTuple_GET_SIZE(args), kw);
#else
        (void) &__Pyx_PyVectorcall_FastCallDict;
        return PyVectorcall_Call(func, args, kw);
#endif
    }
#endif
    if ((cyfunc->flags & __Pyx_CYFUNCTION_CCLASS) && !(cyfunc->flags & __Pyx_CYFUNCTION_STATICMETHOD)) {
        Py_ssize_t argc;
        PyObject *new_args;
        PyObject *self;
#if CYTHON_ASSUME_SAFE_SIZE
        argc = PyTuple_GET_SIZE(args);
#else
        argc = PyTuple_Size(args);
        if (unlikely(argc < 0)) return NULL;
#endif
        new_args = PyTuple_GetSlice(args, 1, argc);
        if (unlikely(!new_args))
            return NULL;
        self = PyTuple_GetItem(args, 0);
        if (unlikely(!self)) {
            Py_DECREF(new_args);
            PyErr_Format(PyExc_TypeError,
                         "unbound method %.200S() needs an argument",
                         cyfunc->func_qualname);
            return NULL;
        }
        result = __Pyx_CyFunction_CallMethod(func, self, new_args, kw);
        Py_DECREF(new_args);
    } else {
        result = __Pyx_CyFunction_Call(func, args, kw);
    }
    return result;
}
#if CYTHON_METH_FASTCALL && (CYTHON_VECTORCALL || CYTHON_BACKPORT_VECTORCALL)
static CYTHON_INLINE int __Pyx_CyFunction_Vectorcall_CheckArgs(__pyx_CyFunctionObject *cyfunc, Py_ssize_t nargs, PyObject *kwnames)
{
    int ret = 0;
    if ((cyfunc->flags & __Pyx_CYFUNCTION_CCLASS) && !(cyfunc->flags & __Pyx_CYFUNCTION_STATICMETHOD)) {
        if (unlikely(nargs < 1)) {
            __Pyx_CyFunction_raise_type_error(
                cyfunc, "needs an argument");
            return -1;
        }
        ret = 1;
    }
    if (unlikely(kwnames) && unlikely(__Pyx_PyTuple_GET_SIZE(kwnames))) {
        __Pyx_CyFunction_raise_type_error(
            cyfunc, "takes no keyword arguments");
        return -1;
    }
    return ret;
}
static PyObject * __Pyx_CyFunction_Vectorcall_NOARGS(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames)
{
    __pyx_CyFunctionObject *cyfunc = (__pyx_CyFunctionObject *)func;
#if CYTHON_BACKPORT_VECTORCALL
    Py_ssize_t nargs = (Py_ssize_t)nargsf;
#else
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
#endif
    PyObject *self;
#if CYTHON_COMPILING_IN_LIMITED_API
    PyCFunction meth = PyCFunction_GetFunction(cyfunc->func);
    if (unlikely(!meth)) return NULL;
#else
    PyCFunction meth = ((PyCFunctionObject*)cyfunc)->m_ml->ml_meth;
#endif
    switch (__Pyx_CyFunction_Vectorcall_CheckArgs(cyfunc, nargs, kwnames)) {
    case 1:
        self = args[0];
        args += 1;
        nargs -= 1;
        break;
    case 0:
#if CYTHON_COMPILING_IN_LIMITED_API
        self = PyCFunction_GetSelf(((__pyx_CyFunctionObject*)cyfunc)->func);
        if (unlikely(!self) && PyErr_Occurred()) return NULL;
#else
        self = ((PyCFunctionObject*)cyfunc)->m_self;
#endif
        break;
    default:
        return NULL;
    }
    if (unlikely(nargs != 0)) {
        __Pyx_CyFunction_raise_argument_count_error(
            cyfunc, "takes no arguments", nargs);
        return NULL;
    }
    return meth(self, NULL);
}
static PyObject * __Pyx_CyFunction_Vectorcall_O(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames)
{
    __pyx_CyFunctionObject *cyfunc = (__pyx_CyFunctionObject *)func;
#if CYTHON_BACKPORT_VECTORCALL
    Py_ssize_t nargs = (Py_ssize_t)nargsf;
#else
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
#endif
    PyObject *self;
#if CYTHON_COMPILING_IN_LIMITED_API
    PyCFunction meth = PyCFunction_GetFunction(cyfunc->func);
    if (unlikely(!meth)) return NULL;
#else
    PyCFunction meth = ((PyCFunctionObject*)cyfunc)->m_ml->ml_meth;
#endif
    switch (__Pyx_CyFunction_Vectorcall_CheckArgs(cyfunc, nargs, kwnames)) {
    case 1:
        self = args[0];
        args += 1;
        nargs -= 1;
        break;
    case 0:
#if CYTHON_COMPILING_IN_LIMITED_API
        self = PyCFunction_GetSelf(((__pyx_CyFunctionObject*)cyfunc)->func);
        if (unlikely(!self) && PyErr_Occurred()) return NULL;
#else
        self = ((PyCFunctionObject*)cyfunc)->m_self;
#endif
        break;
    default:
        return NULL;
    }
    if (unlikely(nargs != 1)) {
        __Pyx_CyFunction_raise_argument_count_error(
            cyfunc, "takes exactly one argument", nargs);
        return NULL;
    }
    return meth(self, args[0]);
}
static PyObject * __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames)
{
    __pyx_CyFunctionObject *cyfunc = (__pyx_CyFunctionObject *)func;
#if CYTHON_BACKPORT_VECTORCALL
    Py_ssize_t nargs = (Py_ssize_t)nargsf;
#else
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
#endif
    PyObject *self;
#if CYTHON_COMPILING_IN_LIMITED_API
    PyCFunction meth = PyCFunction_GetFunction(cyfunc->func);
    if (unlikely(!meth)) return NULL;
#else
    PyCFunction meth = ((PyCFunctionObject*)cyfunc)->m_ml->ml_meth;
#endif
    switch (__Pyx_CyFunction_Vectorcall_CheckArgs(cyfunc, nargs, NULL)) {
    case 1:
        self = args[0];
        args += 1;
        nargs -= 1;
        break;
    case 0:
#if CYTHON_COMPILING_IN_LIMITED_API
        self = PyCFunction_GetSelf(((__pyx_CyFunctionObject*)cyfunc)->func);
        if (unlikely(!self) && PyErr_Occurred()) return NULL;
#else
        self = ((PyCFunctionObject*)cyfunc)->m_self;
#endif
        break;
    default:
        return NULL;
    }
    return ((__Pyx_PyCFunctionFastWithKeywords)(void(*)(void))meth)(self, args, nargs, kwnames);
}
static PyObject * __Pyx_CyFunction_Vectorcall_FASTCALL_KEYWORDS_METHOD(PyObject *func, PyObject *const *args, size_t nargsf, PyObject *kwnames)
{
    __pyx_CyFunctionObject *cyfunc = (__pyx_CyFunctionObject *)func;
    PyTypeObject *cls = (PyTypeObject *) __Pyx_CyFunction_GetClassObj(cyfunc);
#if CYTHON_BACKPORT_VECTORCALL
    Py_ssize_t nargs = (Py_ssize_t)nargsf;
#else
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
#endif
    PyObject *self;
#if CYTHON_COMPILING_IN_LIMITED_API
    PyCFunction meth = PyCFunction_GetFunction(cyfunc->func);
    if (unlikely(!meth)) return NULL;
#else
    PyCFunction meth = ((PyCFunctionObject*)cyfunc)->m_ml->ml_meth;
#endif
    switch (__Pyx_CyFunction_Vectorcall_CheckArgs(cyfunc, nargs, NULL)) {
    case 1:
        self = args[0];
        args += 1;
        nargs -= 1;
        break;
    case 0:
#if CYTHON_COMPILING_IN_LIMITED_API
        self = PyCFunction_GetSelf(((__pyx_CyFunctionObject*)cyfunc)->func);
        if (unlikely(!self) && PyErr_Occurred()) return NULL;
#else
        self = ((PyCFunctionObject*)cyfunc)->m_self;
#endif
        break;
    default:
        return NULL;
    }
    return ((__Pyx_PyCMethod)(void(*)(void))meth)(self, cls, args, (size_t)nargs, kwnames);
}
#endif
static PyType_Slot __pyx_CyFunctionType_slots[] = {
    {Py_tp_dealloc, (void *)__Pyx_CyFunction_dealloc},
    {Py_tp_repr, (void *)__Pyx_CyFunction_repr},
    {Py_tp_call, (void *)__Pyx_CyFunction_CallAsMethod},
    {Py_tp_traverse, (void *)__Pyx_CyFunction_traverse},
    {Py_tp_clear, (void *)__Pyx_CyFunction_clear},
    {Py_tp_methods, (void *)__pyx_CyFunction_methods},
    {Py_tp_members, (void *)__pyx_CyFunction_members},
    {Py_tp_getset, (void *)__pyx_CyFunction_getsets},
    {Py_tp_descr_get, (void *)__Pyx_PyMethod_New},
    {0, 0},
};
static PyType_Spec __pyx_CyFunctionType_spec = {
    __PYX_TYPE_MODULE_PREFIX "cython_function_or_method",
    sizeof(__pyx_CyFunctionObject),
    0,
#ifdef Py_TPFLAGS_METHOD_DESCRIPTOR
    Py_TPFLAGS_METHOD_DESCRIPTOR |
#endif
#if CYTHON_METH_FASTCALL
#if defined(Py_TPFLAGS_HAVE_VECTORCALL)
    Py_TPFLAGS_HAVE_VECTORCALL |
#elif defined(_Py_TPFLAGS_HAVE_VECTORCALL)
    _Py_TPFLAGS_HAVE_VECTORCALL |
#endif
#endif // CYTHON_METH_FASTCALL
#if PY_VERSION_HEX >= 0x030A0000
    Py_TPFLAGS_IMMUTABLETYPE |
#endif
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_BASETYPE,
    __pyx_CyFunctionType_slots
};
static int __pyx_CyFunction_init(PyObject *module) {
    __pyx_mstatetype *mstate = __Pyx_PyModule_GetState(module);
    mstate->__pyx_CyFunctionType = __Pyx_FetchCommonTypeFromSpec(
        mstate->__pyx_CommonTypesMetaclassType, module, &__pyx_CyFunctionType_spec, NULL);
    if (unlikely(mstate->__pyx_CyFunctionType == NULL)) {
        return -1;
    }
    return 0;
}
static CYTHON_INLINE PyObject *__Pyx_CyFunction_InitDefaults(PyObject *func, PyTypeObject *defaults_type) {
    __pyx_CyFunctionObject *m = (__pyx_CyFunctionObject *) func;
    m->defaults = PyObject_CallObject((PyObject*)defaults_type, NULL); // _PyObject_New(defaults_type);
    if (unlikely(!m->defaults))
        return NULL;
    return m->defaults;
}
static CYTHON_INLINE void __Pyx_CyFunction_SetDefaultsTuple(PyObject *func, PyObject *tuple) {
    __pyx_CyFunctionObject *m = (__pyx_CyFunctionObject *) func;
    m->defaults_tuple = tuple;
    Py_INCREF(tuple);
}
static CYTHON_INLINE void __Pyx_CyFunction_SetDefaultsKwDict(PyObject *func, PyObject *dict) {
    __pyx_CyFunctionObject *m = (__pyx_CyFunctionObject *) func;
    m->defaults_kwdict = dict;
    Py_INCREF(dict);
}
static CYTHON_INLINE void __Pyx_CyFunction_SetAnnotationsDict(PyObject *func, PyObject *dict) {
    __pyx_CyFunctionObject *m = (__pyx_CyFunctionObject *) func;
    m->func_annotations = dict;
    Py_INCREF(dict);
}

/* CythonFunction */
static PyObject *__Pyx_CyFunction_New(PyMethodDef *ml, int flags, PyObject* qualname,
                                      PyObject *closure, PyObject *module, PyObject* globals, PyObject* code) {
    PyObject *op = __Pyx_CyFunction_Init(
        PyObject_GC_New(__pyx_CyFunctionObject, __pyx_mstate_global->__pyx_CyFunctionType),
        ml, flags, qualname, closure, module, globals, code
    );
    if (likely(op)) {
        PyObject_GC_Track(op);
    }
    return op;
}

/* PyObjectVectorCallKwBuilder */
#if CYTHON_VECTORCALL
static int __Pyx_VectorcallBuilder_AddArg(PyObject *key, PyObject *value, PyObject *builder, PyObject **args, int n) {
    (void)__Pyx_PyObject_FastCallDict;
    if (__Pyx_PyTuple_SET_ITEM(builder, n, key) != (0)) return -1;
    Py_INCREF(key);
    args[n] = value;
    return 0;
}
CYTHON_UNUSED static int __Pyx_VectorcallBuilder_AddArg_Check(PyObject *key, PyObject *value, PyObject *builder, PyObject **args, int n) {
    (void)__Pyx_VectorcallBuilder_AddArgStr;
    if (unlikely(!PyUnicode_Check(key))) {
        PyErr_SetString(PyExc_TypeError, "keywords must be strings");
        return -1;
    }
    return __Pyx_VectorcallBuilder_AddArg(key, value, builder, args, n);
}
static int __Pyx_VectorcallBuilder_AddArgStr(const char *key, PyObject *value, PyObject *builder, PyObject **args, int n) {
    PyObject *pyKey = PyUnicode_FromString(key);
    if (!pyKey) return -1;
    return __Pyx_VectorcallBuilder_AddArg(pyKey, value, builder, args, n);
}
#else // CYTHON_VECTORCALL
CYTHON_UNUSED static int __Pyx_VectorcallBuilder_AddArg_Check(PyObject *key, PyObject *value, PyObject *builder, CYTHON_UNUSED PyObject **args, CYTHON_UNUSED int n) {
    if (unlikely(!PyUnicode_Check(key))) {
        PyErr_SetString(PyExc_TypeError, "keywords must be strings");
        return -1;
    }
    return PyDict_SetItem(builder, key, value);
}
#endif

/* PyObjectVectorCallMethodKwBuilder */
#if !CYTHON_VECTORCALL || PY_VERSION_HEX < 0x03090000
static PyObject *__Pyx_Object_VectorcallMethod_CallFromBuilder(PyObject *name, PyObject *const *args, size_t nargsf, PyObject *kwnames) {
    PyObject *result;
    PyObject *obj = PyObject_GetAttr(args[0], name);
    if (unlikely(!obj))
        return NULL;
    result = __Pyx_Object_Vectorcall_CallFromBuilder(obj, args+1, nargsf-1, kwnames);
    Py_DECREF(obj);
    return result;
}
#endif

/* PyObjectCallNoArg */
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallNoArg(PyObject *func) {
    PyObject *arg[2] = {NULL, NULL};
    return __Pyx_PyObject_FastCall(func, arg + 1, 0 | __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET);
}

/* PyObjectCallOneArg */
static CYTHON_INLINE PyObject* __Pyx_PyObject_CallOneArg(PyObject *func, PyObject *arg) {
    PyObject *args[2] = {NULL, arg};
    return __Pyx_PyObject_FastCall(func, args+1, 1 | __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET);
}

/* PyObjectGetMethod */
static int __Pyx_PyObject_GetMethod(PyObject *obj, PyObject *name, PyObject **method) {
    PyObject *attr;
#if CYTHON_UNPACK_METHODS && CYTHON_COMPILING_IN_CPYTHON && CYTHON_USE_PYTYPE_LOOKUP
    __Pyx_TypeName type_name;
    PyTypeObject *tp = Py_TYPE(obj);
    PyObject *descr;
    descrgetfunc f = NULL;
    PyObject **dictptr, *dict;
    int meth_found = 0;
    assert (*method == NULL);
    if (unlikely(tp->tp_getattro != PyObject_GenericGetAttr)) {
        attr = __Pyx_PyObject_GetAttrStr(obj, name);
        goto try_unpack;
    }
    if (unlikely(tp->tp_dict == NULL) && unlikely(PyType_Ready(tp) < 0)) {
        return 0;
    }
    descr = _PyType_Lookup(tp, name);
    if (likely(descr != NULL)) {
        Py_INCREF(descr);
#if defined(Py_TPFLAGS_METHOD_DESCRIPTOR) && Py_TPFLAGS_METHOD_DESCRIPTOR
        if (__Pyx_PyType_HasFeature(Py_TYPE(descr), Py_TPFLAGS_METHOD_DESCRIPTOR))
#else
        #ifdef __Pyx_CyFunction_USED
        if (likely(PyFunction_Check(descr) || __Pyx_IS_TYPE(descr, &PyMethodDescr_Type) || __Pyx_CyFunction_Check(descr)))
        #else
        if (likely(PyFunction_Check(descr) || __Pyx_IS_TYPE(descr, &PyMethodDescr_Type)))
        #endif
#endif
        {
            meth_found = 1;
        } else {
            f = Py_TYPE(descr)->tp_descr_get;
            if (f != NULL && PyDescr_IsData(descr)) {
                attr = f(descr, obj, (PyObject *)Py_TYPE(obj));
                Py_DECREF(descr);
                goto try_unpack;
            }
        }
    }
    dictptr = _PyObject_GetDictPtr(obj);
    if (dictptr != NULL && (dict = *dictptr) != NULL) {
        Py_INCREF(dict);
        attr = __Pyx_PyDict_GetItemStr(dict, name);
        if (attr != NULL) {
            Py_INCREF(attr);
            Py_DECREF(dict);
            Py_XDECREF(descr);
            goto try_unpack;
        }
        Py_DECREF(dict);
    }
    if (meth_found) {
        *method = descr;
        return 1;
    }
    if (f != NULL) {
        attr = f(descr, obj, (PyObject *)Py_TYPE(obj));
        Py_DECREF(descr);
        goto try_unpack;
    }
    if (likely(descr != NULL)) {
        *method = descr;
        return 0;
    }
    type_name = __Pyx_PyType_GetFullyQualifiedName(tp);
    PyErr_Format(PyExc_AttributeError,
                 "'" __Pyx_FMT_TYPENAME "' object has no attribute '%U'",
                 type_name, name);
    __Pyx_DECREF_TypeName(type_name);
    return 0;
#else
    attr = __Pyx_PyObject_GetAttrStr(obj, name);
    goto try_unpack;
#endif
try_unpack:
#if CYTHON_UNPACK_METHODS
    if (likely(attr) && PyMethod_Check(attr) && likely(PyMethod_GET_SELF(attr) == obj)) {
        PyObject *function = PyMethod_GET_FUNCTION(attr);
        Py_INCREF(function);
        Py_DECREF(attr);
        *method = function;
        return 1;
    }
#endif
    *method = attr;
    return 0;
}

/* PyObjectCallMethod0 */
static PyObject* __Pyx_PyObject_CallMethod0(PyObject* obj, PyObject* method_name) {
    PyObject *method = NULL, *result = NULL;
    int is_method = __Pyx_PyObject_GetMethod(obj, method_name, &method);
    if (likely(is_method)) {
        result = __Pyx_PyObject_CallOneArg(method, obj);
        Py_DECREF(method);
        return result;
    }
    if (unlikely(!method)) goto bad;
    result = __Pyx_PyObject_CallNoArg(method);
    Py_DECREF(method);
bad:
    return result;
}

/* ValidateBasesTuple */
#if CYTHON_COMPILING_IN_CPYTHON || CYTHON_COMPILING_IN_LIMITED_API || CYTHON_USE_TYPE_SPECS
static int __Pyx_validate_bases_tuple(const char *type_name, Py_ssize_t dictoffset, PyObject *bases) {
    Py_ssize_t i, n;
#if CYTHON_ASSUME_SAFE_SIZE
    n = PyTuple_GET_SIZE(bases);
#else
    n = PyTuple_Size(bases);
    if (unlikely(n < 0)) return -1;
#endif
    for (i = 1; i < n; i++)
    {
        PyTypeObject *b;
#if CYTHON_AVOID_BORROWED_REFS
        PyObject *b0 = PySequence_GetItem(bases, i);
        if (!b0) return -1;
#elif CYTHON_ASSUME_SAFE_MACROS
        PyObject *b0 = PyTuple_GET_ITEM(bases, i);
#else
        PyObject *b0 = PyTuple_GetItem(bases, i);
        if (!b0) return -1;
#endif
        b = (PyTypeObject*) b0;
        if (!__Pyx_PyType_HasFeature(b, Py_TPFLAGS_HEAPTYPE))
        {
            __Pyx_TypeName b_name = __Pyx_PyType_GetFullyQualifiedName(b);
            PyErr_Format(PyExc_TypeError,
                "base class '" __Pyx_FMT_TYPENAME "' is not a heap type", b_name);
            __Pyx_DECREF_TypeName(b_name);
#if CYTHON_AVOID_BORROWED_REFS
            Py_DECREF(b0);
#endif
            return -1;
        }
        if (dictoffset == 0)
        {
            Py_ssize_t b_dictoffset = 0;
#if CYTHON_USE_TYPE_SLOTS
            b_dictoffset = b->tp_dictoffset;
#else
            PyObject *py_b_dictoffset = PyObject_GetAttrString((PyObject*)b, "__dictoffset__");
            if (!py_b_dictoffset) goto dictoffset_return;
            b_dictoffset = PyLong_AsSsize_t(py_b_dictoffset);
            Py_DECREF(py_b_dictoffset);
            if (b_dictoffset == -1 && PyErr_Occurred()) goto dictoffset_return;
#endif
            if (b_dictoffset) {
                {
                    __Pyx_TypeName b_name = __Pyx_PyType_GetFullyQualifiedName(b);
                    PyErr_Format(PyExc_TypeError,
                        "extension type '%.200s' has no __dict__ slot, "
                        "but base type '" __Pyx_FMT_TYPENAME "' has: "
                        "either add 'cdef dict __dict__' to the extension type "
                        "or add '__slots__ = [...]' to the base type",
                        type_name, b_name);
                    __Pyx_DECREF_TypeName(b_name);
                }
#if !CYTHON_USE_TYPE_SLOTS
              dictoffset_return:
#endif
#if CYTHON_AVOID_BORROWED_REFS
                Py_DECREF(b0);
#endif
                return -1;
            }
        }
#if CYTHON_AVOID_BORROWED_REFS
        Py_DECREF(b0);
#endif
    }
    return 0;
}
#endif

/* PyType_Ready */
CYTHON_UNUSED static int __Pyx_PyType_HasMultipleInheritance(PyTypeObject *t) {
    while (t) {
        PyObject *bases = __Pyx_PyType_GetSlot(t, tp_bases, PyObject*);
        if (bases) {
            return 1;
        }
        t = __Pyx_PyType_GetSlot(t, tp_base, PyTypeObject*);
    }
    return 0;
}
static int __Pyx_PyType_Ready(PyTypeObject *t) {
#if CYTHON_USE_TYPE_SPECS || !CYTHON_COMPILING_IN_CPYTHON || defined(PYSTON_MAJOR_VERSION)
    (void)__Pyx_PyObject_CallMethod0;
#if CYTHON_USE_TYPE_SPECS
    (void)__Pyx_validate_bases_tuple;
#endif
    return PyType_Ready(t);
#else
    int r;
    if (!__Pyx_PyType_HasMultipleInheritance(t)) {
        return PyType_Ready(t);
    }
    PyObject *bases = __Pyx_PyType_GetSlot(t, tp_bases, PyObject*);
    if (bases && unlikely(__Pyx_validate_bases_tuple(t->tp_name, t->tp_dictoffset, bases) == -1))
        return -1;
#if !defined(PYSTON_MAJOR_VERSION)
    {
        int gc_was_enabled;
    #if PY_VERSION_HEX >= 0x030A00b1
        gc_was_enabled = PyGC_Disable();
        (void)__Pyx_PyObject_CallMethod0;
    #else
        PyObject *ret, *py_status;
        PyObject *gc = NULL;
        #if (!CYTHON_COMPILING_IN_PYPY || PYPY_VERSION_NUM+0 >= 0x07030400) &&\
                !CYTHON_COMPILING_IN_GRAAL
        gc = PyImport_GetModule(__pyx_mstate_global->__pyx_kp_u_gc);
        #endif
        if (unlikely(!gc)) gc = PyImport_Import(__pyx_mstate_global->__pyx_kp_u_gc);
        if (unlikely(!gc)) return -1;
        py_status = __Pyx_PyObject_CallMethod0(gc, __pyx_mstate_global->__pyx_kp_u_isenabled);
        if (unlikely(!py_status)) {
            Py_DECREF(gc);
            return -1;
        }
        gc_was_enabled = __Pyx_PyObject_IsTrue(py_status);
        Py_DECREF(py_status);
        if (gc_was_enabled > 0) {
            ret = __Pyx_PyObject_CallMethod0(gc, __pyx_mstate_global->__pyx_kp_u_disable);
            if (unlikely(!ret)) {
                Py_DECREF(gc);
                return -1;
            }
            Py_DECREF(ret);
        } else if (unlikely(gc_was_enabled == -1)) {
            Py_DECREF(gc);
            return -1;
        }
    #endif
        t->tp_flags |= Py_TPFLAGS_HEAPTYPE;
#if PY_VERSION_HEX >= 0x030A0000
        t->tp_flags |= Py_TPFLAGS_IMMUTABLETYPE;
#endif
#else
        (void)__Pyx_PyObject_CallMethod0;
#endif
    r = PyType_Ready(t);
#if !defined(PYSTON_MAJOR_VERSION)
        t->tp_flags &= ~Py_TPFLAGS_HEAPTYPE;
    #if PY_VERSION_HEX >= 0x030A00b1
        if (gc_was_enabled)
            PyGC_Enable();
    #else
        if (gc_was_enabled) {
            PyObject *tp, *v, *tb;
            PyErr_Fetch(&tp, &v, &tb);
            ret = __Pyx_PyObject_CallMethod0(gc, __pyx_mstate_global->__pyx_kp_u_enable);
            if (likely(ret || r == -1)) {
                Py_XDECREF(ret);
                PyErr_Restore(tp, v, tb);
            } else {
                Py_XDECREF(tp);
                Py_XDECREF(v);
                Py_XDECREF(tb);
                r = -1;
            }
        }
        Py_DECREF(gc);
    #endif
    }
#endif
    return r;
#endif
}

/* PyDictVersioning */
#if CYTHON_USE_DICT_VERSIONS && CYTHON_USE_TYPE_SLOTS
static CYTHON_INLINE PY_UINT64_T __Pyx_get_tp_dict_version(PyObject *obj) {
    PyObject *dict = Py_TYPE(obj)->tp_dict;
    return likely(dict) ? __PYX_GET_DICT_VERSION(dict) : 0;
}
static CYTHON_INLINE PY_UINT64_T __Pyx_get_object_dict_version(PyObject *obj) {
    PyObject **dictptr = NULL;
    Py_ssize_t offset = Py_TYPE(obj)->tp_dictoffset;
    if (offset) {
#if CYTHON_COMPILING_IN_CPYTHON
        dictptr = (likely(offset > 0)) ? (PyObject **) ((char *)obj + offset) : _PyObject_GetDictPtr(obj);
#else
        dictptr = _PyObject_GetDictPtr(obj);
#endif
    }
    return (dictptr && *dictptr) ? __PYX_GET_DICT_VERSION(*dictptr) : 0;
}
static CYTHON_INLINE int __Pyx_object_dict_version_matches(PyObject* obj, PY_UINT64_T tp_dict_version, PY_UINT64_T obj_dict_version) {
    PyObject *dict = Py_TYPE(obj)->tp_dict;
    if (unlikely(!dict) || unlikely(tp_dict_version != __PYX_GET_DICT_VERSION(dict)))
        return 0;
    return obj_dict_version == __Pyx_get_object_dict_version(obj);
}
#endif

/* CLineInTraceback */
#if CYTHON_CLINE_IN_TRACEBACK && CYTHON_CLINE_IN_TRACEBACK_RUNTIME
static int __Pyx_CLineForTraceback(PyThreadState *tstate, int c_line) {
    PyObject *use_cline;
    PyObject *ptype, *pvalue, *ptraceback;
#if CYTHON_COMPILING_IN_CPYTHON
    PyObject **cython_runtime_dict;
#endif
    CYTHON_MAYBE_UNUSED_VAR(tstate);
    if (unlikely(!__pyx_mstate_global->__pyx_cython_runtime)) {
        return c_line;
    }
    __Pyx_ErrFetchInState(tstate, &ptype, &pvalue, &ptraceback);
#if CYTHON_COMPILING_IN_CPYTHON
    cython_runtime_dict = _PyObject_GetDictPtr(__pyx_mstate_global->__pyx_cython_runtime);
    if (likely(cython_runtime_dict)) {
        __Pyx_BEGIN_CRITICAL_SECTION(*cython_runtime_dict);
        __PYX_PY_DICT_LOOKUP_IF_MODIFIED(
            use_cline, *cython_runtime_dict,
            __Pyx_PyDict_GetItemStr(*cython_runtime_dict, __pyx_mstate_global->__pyx_n_u_cline_in_traceback))
        Py_XINCREF(use_cline);
        __Pyx_END_CRITICAL_SECTION();
    } else
#endif
    {
      PyObject *use_cline_obj = __Pyx_PyObject_GetAttrStrNoError(__pyx_mstate_global->__pyx_cython_runtime, __pyx_mstate_global->__pyx_n_u_cline_in_traceback);
      if (use_cline_obj) {
        use_cline = PyObject_Not(use_cline_obj) ? Py_False : Py_True;
        Py_INCREF(use_cline);
        Py_DECREF(use_cline_obj);
      } else {
        PyErr_Clear();
        use_cline = NULL;
      }
    }
    if (!use_cline) {
        c_line = 0;
        (void) PyObject_SetAttr(__pyx_mstate_global->__pyx_cython_runtime, __pyx_mstate_global->__pyx_n_u_cline_in_traceback, Py_False);
    }
    else if (use_cline == Py_False || (use_cline != Py_True && PyObject_Not(use_cline) != 0)) {
        c_line = 0;
    }
    Py_XDECREF(use_cline);
    __Pyx_ErrRestoreInState(tstate, ptype, pvalue, ptraceback);
    return c_line;
}
#endif

/* CodeObjectCache */
static int __pyx_bisect_code_objects(__Pyx_CodeObjectCacheEntry* entries, int count, int code_line) {
    int start = 0, mid = 0, end = count - 1;
    if (end >= 0 && code_line > entries[end].code_line) {
        return count;
    }
    while (start < end) {
        mid = start + (end - start) / 2;
        if (code_line < entries[mid].code_line) {
            end = mid;
        } else if (code_line > entries[mid].code_line) {
             start = mid + 1;
        } else {
            return mid;
        }
    }
    if (code_line <= entries[mid].code_line) {
        return mid;
    } else {
        return mid + 1;
    }
}
static __Pyx_CachedCodeObjectType *__pyx__find_code_object(struct __Pyx_CodeObjectCache *code_cache, int code_line) {
    __Pyx_CachedCodeObjectType* code_object;
    int pos;
    if (unlikely(!code_line) || unlikely(!code_cache->entries)) {
        return NULL;
    }
    pos = __pyx_bisect_code_objects(code_cache->entries, code_cache->count, code_line);
    if (unlikely(pos >= code_cache->count) || unlikely(code_cache->entries[pos].code_line != code_line)) {
        return NULL;
    }
    code_object = code_cache->entries[pos].code_object;
    Py_INCREF(code_object);
    return code_object;
}
static __Pyx_CachedCodeObjectType *__pyx_find_code_object(int code_line) {
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING && !CYTHON_ATOMICS
    (void)__pyx__find_code_object;
    return NULL; // Most implementation should have atomics. But otherwise, don't make it thread-safe, just miss.
#else
    struct __Pyx_CodeObjectCache *code_cache = &__pyx_mstate_global->__pyx_code_cache;
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    __pyx_nonatomic_int_type old_count = __pyx_atomic_incr_acq_rel(&code_cache->accessor_count);
    if (old_count < 0) {
        __pyx_atomic_decr_acq_rel(&code_cache->accessor_count);
        return NULL;
    }
#endif
    __Pyx_CachedCodeObjectType *result = __pyx__find_code_object(code_cache, code_line);
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    __pyx_atomic_decr_acq_rel(&code_cache->accessor_count);
#endif
    return result;
#endif
}
static void __pyx__insert_code_object(struct __Pyx_CodeObjectCache *code_cache, int code_line, __Pyx_CachedCodeObjectType* code_object)
{
    int pos, i;
    __Pyx_CodeObjectCacheEntry* entries = code_cache->entries;
    if (unlikely(!code_line)) {
        return;
    }
    if (unlikely(!entries)) {
        entries = (__Pyx_CodeObjectCacheEntry*)PyMem_Malloc(64*sizeof(__Pyx_CodeObjectCacheEntry));
        if (likely(entries)) {
            code_cache->entries = entries;
            code_cache->max_count = 64;
            code_cache->count = 1;
            entries[0].code_line = code_line;
            entries[0].code_object = code_object;
            Py_INCREF(code_object);
        }
        return;
    }
    pos = __pyx_bisect_code_objects(code_cache->entries, code_cache->count, code_line);
    if ((pos < code_cache->count) && unlikely(code_cache->entries[pos].code_line == code_line)) {
        __Pyx_CachedCodeObjectType* tmp = entries[pos].code_object;
        entries[pos].code_object = code_object;
        Py_INCREF(code_object);
        Py_DECREF(tmp);
        return;
    }
    if (code_cache->count == code_cache->max_count) {
        int new_max = code_cache->max_count + 64;
        entries = (__Pyx_CodeObjectCacheEntry*)PyMem_Realloc(
            code_cache->entries, ((size_t)new_max) * sizeof(__Pyx_CodeObjectCacheEntry));
        if (unlikely(!entries)) {
            return;
        }
        code_cache->entries = entries;
        code_cache->max_count = new_max;
    }
    for (i=code_cache->count; i>pos; i--) {
        entries[i] = entries[i-1];
    }
    entries[pos].code_line = code_line;
    entries[pos].code_object = code_object;
    code_cache->count++;
    Py_INCREF(code_object);
}
static void __pyx_insert_code_object(int code_line, __Pyx_CachedCodeObjectType* code_object) {
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING && !CYTHON_ATOMICS
    (void)__pyx__insert_code_object;
    return; // Most implementation should have atomics. But otherwise, don't make it thread-safe, just fail.
#else
    struct __Pyx_CodeObjectCache *code_cache = &__pyx_mstate_global->__pyx_code_cache;
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    __pyx_nonatomic_int_type expected = 0;
    if (!__pyx_atomic_int_cmp_exchange(&code_cache->accessor_count, &expected, INT_MIN)) {
        return;
    }
#endif
    __pyx__insert_code_object(code_cache, code_line, code_object);
#if CYTHON_COMPILING_IN_CPYTHON_FREETHREADING
    __pyx_atomic_sub(&code_cache->accessor_count, INT_MIN);
#endif
#endif
}

/* AddTraceback */
#include "compile.h"
#include "frameobject.h"
#include "traceback.h"
#if PY_VERSION_HEX >= 0x030b00a6 && !CYTHON_COMPILING_IN_LIMITED_API && !defined(PYPY_VERSION)
  #ifndef Py_BUILD_CORE
    #define Py_BUILD_CORE 1
  #endif
  #include "internal/pycore_frame.h"
#endif
#if CYTHON_COMPILING_IN_LIMITED_API
static PyObject *__Pyx_PyCode_Replace_For_AddTraceback(PyObject *code, PyObject *scratch_dict,
                                                       PyObject *firstlineno, PyObject *name) {
    PyObject *replace = NULL;
    if (unlikely(PyDict_SetItemString(scratch_dict, "co_firstlineno", firstlineno))) return NULL;
    if (unlikely(PyDict_SetItemString(scratch_dict, "co_name", name))) return NULL;
    replace = PyObject_GetAttrString(code, "replace");
    if (likely(replace)) {
        PyObject *result = PyObject_Call(replace, __pyx_mstate_global->__pyx_empty_tuple, scratch_dict);
        Py_DECREF(replace);
        return result;
    }
    PyErr_Clear();
    return NULL;
}
static void __Pyx_AddTraceback(const char *funcname, int c_line,
                               int py_line, const char *filename) {
    PyObject *code_object = NULL, *py_py_line = NULL, *py_funcname = NULL, *dict = NULL;
    PyObject *replace = NULL, *getframe = NULL, *frame = NULL;
    PyObject *exc_type, *exc_value, *exc_traceback;
    int success = 0;
    if (c_line) {
        (void) __pyx_cfilenm;
        (void) __Pyx_CLineForTraceback(__Pyx_PyThreadState_Current, c_line);
    }
    PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);
    code_object = __pyx_find_code_object(c_line ? -c_line : py_line);
    if (!code_object) {
        code_object = Py_CompileString("_getframe()", filename, Py_eval_input);
        if (unlikely(!code_object)) goto bad;
        py_py_line = PyLong_FromLong(py_line);
        if (unlikely(!py_py_line)) goto bad;
        py_funcname = PyUnicode_FromString(funcname);
        if (unlikely(!py_funcname)) goto bad;
        dict = PyDict_New();
        if (unlikely(!dict)) goto bad;
        {
            PyObject *old_code_object = code_object;
            code_object = __Pyx_PyCode_Replace_For_AddTraceback(code_object, dict, py_py_line, py_funcname);
            Py_DECREF(old_code_object);
        }
        if (unlikely(!code_object)) goto bad;
        __pyx_insert_code_object(c_line ? -c_line : py_line, code_object);
    } else {
        dict = PyDict_New();
    }
    getframe = PySys_GetObject("_getframe");
    if (unlikely(!getframe)) goto bad;
    if (unlikely(PyDict_SetItemString(dict, "_getframe", getframe))) goto bad;
    frame = PyEval_EvalCode(code_object, dict, dict);
    if (unlikely(!frame) || frame == Py_None) goto bad;
    success = 1;
  bad:
    PyErr_Restore(exc_type, exc_value, exc_traceback);
    Py_XDECREF(code_object);
    Py_XDECREF(py_py_line);
    Py_XDECREF(py_funcname);
    Py_XDECREF(dict);
    Py_XDECREF(replace);
    if (success) {
        PyTraceBack_Here(
            (struct _frame*)frame);
    }
    Py_XDECREF(frame);
}
#else
static PyCodeObject* __Pyx_CreateCodeObjectForTraceback(
            const char *funcname, int c_line,
            int py_line, const char *filename) {
    PyCodeObject *py_code = NULL;
    PyObject *py_funcname = NULL;
    if (c_line) {
        py_funcname = PyUnicode_FromFormat( "%s (%s:%d)", funcname, __pyx_cfilenm, c_line);
        if (!py_funcname) goto bad;
        funcname = PyUnicode_AsUTF8(py_funcname);
        if (!funcname) goto bad;
    }
    py_code = PyCode_NewEmpty(filename, funcname, py_line);
    Py_XDECREF(py_funcname);
    return py_code;
bad:
    Py_XDECREF(py_funcname);
    return NULL;
}
static void __Pyx_AddTraceback(const char *funcname, int c_line,
                               int py_line, const char *filename) {
    PyCodeObject *py_code = 0;
    PyFrameObject *py_frame = 0;
    PyThreadState *tstate = __Pyx_PyThreadState_Current;
    PyObject *ptype, *pvalue, *ptraceback;
    if (c_line) {
        c_line = __Pyx_CLineForTraceback(tstate, c_line);
    }
    py_code = __pyx_find_code_object(c_line ? -c_line : py_line);
    if (!py_code) {
        __Pyx_ErrFetchInState(tstate, &ptype, &pvalue, &ptraceback);
        py_code = __Pyx_CreateCodeObjectForTraceback(
            funcname, c_line, py_line, filename);
        if (!py_code) {
            /* If the code object creation fails, then we should clear the
               fetched exception references and propagate the new exception */
            Py_XDECREF(ptype);
            Py_XDECREF(pvalue);
            Py_XDECREF(ptraceback);
            goto bad;
        }
        __Pyx_ErrRestoreInState(tstate, ptype, pvalue, ptraceback);
        __pyx_insert_code_object(c_line ? -c_line : py_line, py_code);
    }
    py_frame = PyFrame_New(
        tstate,            /*PyThreadState *tstate,*/
        py_code,           /*PyCodeObject *code,*/
        __pyx_mstate_global->__pyx_d,    /*PyObject *globals,*/
        0                  /*PyObject *locals*/
    );
    if (!py_frame) goto bad;
    __Pyx_PyFrame_SetLineNumber(py_frame, py_line);
    PyTraceBack_Here(py_frame);
bad:
    Py_XDECREF(py_code);
    Py_XDECREF(py_frame);
}
#endif

/* CIntFromPyVerify */
#define __PYX_VERIFY_RETURN_INT(target_type, func_type, func_value)\
    __PYX__VERIFY_RETURN_INT(target_type, func_type, func_value, 0)
#define __PYX_VERIFY_RETURN_INT_EXC(target_type, func_type, func_value)\
    __PYX__VERIFY_RETURN_INT(target_type, func_type, func_value, 1)
#define __PYX__VERIFY_RETURN_INT(target_type, func_type, func_value, exc)\
    {\
        func_type value = func_value;\
        if (sizeof(target_type) < sizeof(func_type)) {\
            if (unlikely(value != (func_type) (target_type) value)) {\
                func_type zero = 0;\
                if (exc && unlikely(value == (func_type)-1 && PyErr_Occurred()))\
                    return (target_type) -1;\
                if (is_unsigned && unlikely(value < zero))\
                    goto raise_neg_overflow;\
                else\
                    goto raise_overflow;\
            }\
        }\
        return (target_type) value;\
    }

/* CIntFromPy */
static CYTHON_INLINE int __Pyx_PyLong_As_int(PyObject *x) {
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#endif
    const int neg_one = (int) -1, const_zero = (int) 0;
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic pop
#endif
    const int is_unsigned = neg_one > const_zero;
    if (unlikely(!PyLong_Check(x))) {
        int val;
        PyObject *tmp = __Pyx_PyNumber_Long(x);
        if (!tmp) return (int) -1;
        val = __Pyx_PyLong_As_int(tmp);
        Py_DECREF(tmp);
        return val;
    }
    if (is_unsigned) {
#if CYTHON_USE_PYLONG_INTERNALS
        if (unlikely(__Pyx_PyLong_IsNeg(x))) {
            goto raise_neg_overflow;
        } else if (__Pyx_PyLong_IsCompact(x)) {
            __PYX_VERIFY_RETURN_INT(int, __Pyx_compact_upylong, __Pyx_PyLong_CompactValueUnsigned(x))
        } else {
            const digit* digits = __Pyx_PyLong_Digits(x);
            assert(__Pyx_PyLong_DigitCount(x) > 1);
            switch (__Pyx_PyLong_DigitCount(x)) {
                case 2:
                    if ((8 * sizeof(int) > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) >= 2 * PyLong_SHIFT)) {
                            return (int) (((((int)digits[1]) << PyLong_SHIFT) | (int)digits[0]));
                        }
                    }
                    break;
                case 3:
                    if ((8 * sizeof(int) > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) >= 3 * PyLong_SHIFT)) {
                            return (int) (((((((int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0]));
                        }
                    }
                    break;
                case 4:
                    if ((8 * sizeof(int) > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) >= 4 * PyLong_SHIFT)) {
                            return (int) (((((((((int)digits[3]) << PyLong_SHIFT) | (int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0]));
                        }
                    }
                    break;
            }
        }
#endif
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX < 0x030C00A7
        if (unlikely(Py_SIZE(x) < 0)) {
            goto raise_neg_overflow;
        }
#else
        {
            int result = PyObject_RichCompareBool(x, Py_False, Py_LT);
            if (unlikely(result < 0))
                return (int) -1;
            if (unlikely(result == 1))
                goto raise_neg_overflow;
        }
#endif
        if ((sizeof(int) <= sizeof(unsigned long))) {
            __PYX_VERIFY_RETURN_INT_EXC(int, unsigned long, PyLong_AsUnsignedLong(x))
#ifdef HAVE_LONG_LONG
        } else if ((sizeof(int) <= sizeof(unsigned PY_LONG_LONG))) {
            __PYX_VERIFY_RETURN_INT_EXC(int, unsigned PY_LONG_LONG, PyLong_AsUnsignedLongLong(x))
#endif
        }
    } else {
#if CYTHON_USE_PYLONG_INTERNALS
        if (__Pyx_PyLong_IsCompact(x)) {
            __PYX_VERIFY_RETURN_INT(int, __Pyx_compact_pylong, __Pyx_PyLong_CompactValue(x))
        } else {
            const digit* digits = __Pyx_PyLong_Digits(x);
            assert(__Pyx_PyLong_DigitCount(x) > 1);
            switch (__Pyx_PyLong_SignedDigitCount(x)) {
                case -2:
                    if ((8 * sizeof(int) - 1 > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, long, -(long) (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 2 * PyLong_SHIFT)) {
                            return (int) (((int)-1)*(((((int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
                case 2:
                    if ((8 * sizeof(int) > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 2 * PyLong_SHIFT)) {
                            return (int) ((((((int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
                case -3:
                    if ((8 * sizeof(int) - 1 > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, long, -(long) (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 3 * PyLong_SHIFT)) {
                            return (int) (((int)-1)*(((((((int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
                case 3:
                    if ((8 * sizeof(int) > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 3 * PyLong_SHIFT)) {
                            return (int) ((((((((int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
                case -4:
                    if ((8 * sizeof(int) - 1 > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, long, -(long) (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 4 * PyLong_SHIFT)) {
                            return (int) (((int)-1)*(((((((((int)digits[3]) << PyLong_SHIFT) | (int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
                case 4:
                    if ((8 * sizeof(int) > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(int, unsigned long, (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(int) - 1 > 4 * PyLong_SHIFT)) {
                            return (int) ((((((((((int)digits[3]) << PyLong_SHIFT) | (int)digits[2]) << PyLong_SHIFT) | (int)digits[1]) << PyLong_SHIFT) | (int)digits[0])));
                        }
                    }
                    break;
            }
        }
#endif
        if ((sizeof(int) <= sizeof(long))) {
            __PYX_VERIFY_RETURN_INT_EXC(int, long, PyLong_AsLong(x))
#ifdef HAVE_LONG_LONG
        } else if ((sizeof(int) <= sizeof(PY_LONG_LONG))) {
            __PYX_VERIFY_RETURN_INT_EXC(int, PY_LONG_LONG, PyLong_AsLongLong(x))
#endif
        }
    }
    {
        int val;
        int ret = -1;
#if PY_VERSION_HEX >= 0x030d00A6 && !CYTHON_COMPILING_IN_LIMITED_API
        Py_ssize_t bytes_copied = PyLong_AsNativeBytes(
            x, &val, sizeof(val), Py_ASNATIVEBYTES_NATIVE_ENDIAN | (is_unsigned ? Py_ASNATIVEBYTES_UNSIGNED_BUFFER | Py_ASNATIVEBYTES_REJECT_NEGATIVE : 0));
        if (unlikely(bytes_copied == -1)) {
        } else if (unlikely(bytes_copied > (Py_ssize_t) sizeof(val))) {
            goto raise_overflow;
        } else {
            ret = 0;
        }
#elif PY_VERSION_HEX < 0x030d0000 && !(CYTHON_COMPILING_IN_PYPY || CYTHON_COMPILING_IN_LIMITED_API) || defined(_PyLong_AsByteArray)
        int one = 1; int is_little = (int)*(unsigned char *)&one;
        unsigned char *bytes = (unsigned char *)&val;
        ret = _PyLong_AsByteArray((PyLongObject *)x,
                                    bytes, sizeof(val),
                                    is_little, !is_unsigned);
#else
        PyObject *v;
        PyObject *stepval = NULL, *mask = NULL, *shift = NULL;
        int bits, remaining_bits, is_negative = 0;
        int chunk_size = (sizeof(long) < 8) ? 30 : 62;
        if (likely(PyLong_CheckExact(x))) {
            v = __Pyx_NewRef(x);
        } else {
            v = PyNumber_Long(x);
            if (unlikely(!v)) return (int) -1;
            assert(PyLong_CheckExact(v));
        }
        {
            int result = PyObject_RichCompareBool(v, Py_False, Py_LT);
            if (unlikely(result < 0)) {
                Py_DECREF(v);
                return (int) -1;
            }
            is_negative = result == 1;
        }
        if (is_unsigned && unlikely(is_negative)) {
            Py_DECREF(v);
            goto raise_neg_overflow;
        } else if (is_negative) {
            stepval = PyNumber_Invert(v);
            Py_DECREF(v);
            if (unlikely(!stepval))
                return (int) -1;
        } else {
            stepval = v;
        }
        v = NULL;
        val = (int) 0;
        mask = PyLong_FromLong((1L << chunk_size) - 1); if (unlikely(!mask)) goto done;
        shift = PyLong_FromLong(chunk_size); if (unlikely(!shift)) goto done;
        for (bits = 0; bits < (int) sizeof(int) * 8 - chunk_size; bits += chunk_size) {
            PyObject *tmp, *digit;
            long idigit;
            digit = PyNumber_And(stepval, mask);
            if (unlikely(!digit)) goto done;
            idigit = PyLong_AsLong(digit);
            Py_DECREF(digit);
            if (unlikely(idigit < 0)) goto done;
            val |= ((int) idigit) << bits;
            tmp = PyNumber_Rshift(stepval, shift);
            if (unlikely(!tmp)) goto done;
            Py_DECREF(stepval); stepval = tmp;
        }
        Py_DECREF(shift); shift = NULL;
        Py_DECREF(mask); mask = NULL;
        {
            long idigit = PyLong_AsLong(stepval);
            if (unlikely(idigit < 0)) goto done;
            remaining_bits = ((int) sizeof(int) * 8) - bits - (is_unsigned ? 0 : 1);
            if (unlikely(idigit >= (1L << remaining_bits)))
                goto raise_overflow;
            val |= ((int) idigit) << bits;
        }
        if (!is_unsigned) {
            if (unlikely(val & (((int) 1) << (sizeof(int) * 8 - 1))))
                goto raise_overflow;
            if (is_negative)
                val = ~val;
        }
        ret = 0;
    done:
        Py_XDECREF(shift);
        Py_XDECREF(mask);
        Py_XDECREF(stepval);
#endif
        if (unlikely(ret))
            return (int) -1;
        return val;
    }
raise_overflow:
    PyErr_SetString(PyExc_OverflowError,
        "value too large to convert to int");
    return (int) -1;
raise_neg_overflow:
    PyErr_SetString(PyExc_OverflowError,
        "can't convert negative value to int");
    return (int) -1;
}

/* CIntToPy */
static CYTHON_INLINE PyObject* __Pyx_PyLong_From_unsigned_PY_LONG_LONG(unsigned PY_LONG_LONG value) {
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#endif
    const unsigned PY_LONG_LONG neg_one = (unsigned PY_LONG_LONG) -1, const_zero = (unsigned PY_LONG_LONG) 0;
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic pop
#endif
    const int is_unsigned = neg_one > const_zero;
    if (is_unsigned) {
        if (sizeof(unsigned PY_LONG_LONG) < sizeof(long)) {
            return PyLong_FromLong((long) value);
        } else if (sizeof(unsigned PY_LONG_LONG) <= sizeof(unsigned long)) {
            return PyLong_FromUnsignedLong((unsigned long) value);
#if defined(HAVE_LONG_LONG) && !CYTHON_COMPILING_IN_PYPY
        } else if (sizeof(unsigned PY_LONG_LONG) <= sizeof(unsigned PY_LONG_LONG)) {
            return PyLong_FromUnsignedLongLong((unsigned PY_LONG_LONG) value);
#endif
        }
    } else {
        if (sizeof(unsigned PY_LONG_LONG) <= sizeof(long)) {
            return PyLong_FromLong((long) value);
#ifdef HAVE_LONG_LONG
        } else if (sizeof(unsigned PY_LONG_LONG) <= sizeof(PY_LONG_LONG)) {
            return PyLong_FromLongLong((PY_LONG_LONG) value);
#endif
        }
    }
    {
        unsigned char *bytes = (unsigned char *)&value;
#if !CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX >= 0x030d00A4
        if (is_unsigned) {
            return PyLong_FromUnsignedNativeBytes(bytes, sizeof(value), -1);
        } else {
            return PyLong_FromNativeBytes(bytes, sizeof(value), -1);
        }
#elif !CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX < 0x030d0000
        int one = 1; int little = (int)*(unsigned char *)&one;
        return _PyLong_FromByteArray(bytes, sizeof(unsigned PY_LONG_LONG),
                                     little, !is_unsigned);
#else
        int one = 1; int little = (int)*(unsigned char *)&one;
        PyObject *from_bytes, *result = NULL, *kwds = NULL;
        PyObject *py_bytes = NULL, *order_str = NULL;
        from_bytes = PyObject_GetAttrString((PyObject*)&PyLong_Type, "from_bytes");
        if (!from_bytes) return NULL;
        py_bytes = PyBytes_FromStringAndSize((char*)bytes, sizeof(unsigned PY_LONG_LONG));
        if (!py_bytes) goto limited_bad;
        order_str = PyUnicode_FromString(little ? "little" : "big");
        if (!order_str) goto limited_bad;
        {
            PyObject *args[3+(CYTHON_VECTORCALL ? 1 : 0)] = { NULL, py_bytes, order_str };
            if (!is_unsigned) {
                kwds = __Pyx_MakeVectorcallBuilderKwds(1);
                if (!kwds) goto limited_bad;
                if (__Pyx_VectorcallBuilder_AddArgStr("signed", __Pyx_NewRef(Py_True), kwds, args+3, 0) < 0) goto limited_bad;
            }
            result = __Pyx_Object_Vectorcall_CallFromBuilder(from_bytes, args+1, 2 | __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET, kwds);
        }
        limited_bad:
        Py_XDECREF(kwds);
        Py_XDECREF(order_str);
        Py_XDECREF(py_bytes);
        Py_XDECREF(from_bytes);
        return result;
#endif
    }
}

/* FormatTypeName */
#if CYTHON_COMPILING_IN_LIMITED_API && __PYX_LIMITED_VERSION_HEX < 0x030d0000
static __Pyx_TypeName
__Pyx_PyType_GetFullyQualifiedName(PyTypeObject* tp)
{
    PyObject *module = NULL, *name = NULL, *result = NULL;
    #if __PYX_LIMITED_VERSION_HEX < 0x030b0000
    name = __Pyx_PyObject_GetAttrStr((PyObject *)tp,
                                               __pyx_mstate_global->__pyx_n_u_qualname);
    #else
    name = PyType_GetQualName(tp);
    #endif
    if (unlikely(name == NULL) || unlikely(!PyUnicode_Check(name))) goto bad;
    module = __Pyx_PyObject_GetAttrStr((PyObject *)tp,
                                               __pyx_mstate_global->__pyx_n_u_module);
    if (unlikely(module == NULL) || unlikely(!PyUnicode_Check(module))) goto bad;
    if (PyUnicode_CompareWithASCIIString(module, "builtins") == 0) {
        result = name;
        name = NULL;
        goto done;
    }
    result = PyUnicode_FromFormat("%U.%U", module, name);
    if (unlikely(result == NULL)) goto bad;
  done:
    Py_XDECREF(name);
    Py_XDECREF(module);
    return result;
  bad:
    PyErr_Clear();
    if (name) {
        result = name;
        name = NULL;
    } else {
        result = __Pyx_NewRef(__pyx_mstate_global->__pyx_kp_u_);
    }
    goto done;
}
#endif

/* CIntToPy */
static CYTHON_INLINE PyObject* __Pyx_PyLong_From_long(long value) {
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#endif
    const long neg_one = (long) -1, const_zero = (long) 0;
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic pop
#endif
    const int is_unsigned = neg_one > const_zero;
    if (is_unsigned) {
        if (sizeof(long) < sizeof(long)) {
            return PyLong_FromLong((long) value);
        } else if (sizeof(long) <= sizeof(unsigned long)) {
            return PyLong_FromUnsignedLong((unsigned long) value);
#if defined(HAVE_LONG_LONG) && !CYTHON_COMPILING_IN_PYPY
        } else if (sizeof(long) <= sizeof(unsigned PY_LONG_LONG)) {
            return PyLong_FromUnsignedLongLong((unsigned PY_LONG_LONG) value);
#endif
        }
    } else {
        if (sizeof(long) <= sizeof(long)) {
            return PyLong_FromLong((long) value);
#ifdef HAVE_LONG_LONG
        } else if (sizeof(long) <= sizeof(PY_LONG_LONG)) {
            return PyLong_FromLongLong((PY_LONG_LONG) value);
#endif
        }
    }
    {
        unsigned char *bytes = (unsigned char *)&value;
#if !CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX >= 0x030d00A4
        if (is_unsigned) {
            return PyLong_FromUnsignedNativeBytes(bytes, sizeof(value), -1);
        } else {
            return PyLong_FromNativeBytes(bytes, sizeof(value), -1);
        }
#elif !CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX < 0x030d0000
        int one = 1; int little = (int)*(unsigned char *)&one;
        return _PyLong_FromByteArray(bytes, sizeof(long),
                                     little, !is_unsigned);
#else
        int one = 1; int little = (int)*(unsigned char *)&one;
        PyObject *from_bytes, *result = NULL, *kwds = NULL;
        PyObject *py_bytes = NULL, *order_str = NULL;
        from_bytes = PyObject_GetAttrString((PyObject*)&PyLong_Type, "from_bytes");
        if (!from_bytes) return NULL;
        py_bytes = PyBytes_FromStringAndSize((char*)bytes, sizeof(long));
        if (!py_bytes) goto limited_bad;
        order_str = PyUnicode_FromString(little ? "little" : "big");
        if (!order_str) goto limited_bad;
        {
            PyObject *args[3+(CYTHON_VECTORCALL ? 1 : 0)] = { NULL, py_bytes, order_str };
            if (!is_unsigned) {
                kwds = __Pyx_MakeVectorcallBuilderKwds(1);
                if (!kwds) goto limited_bad;
                if (__Pyx_VectorcallBuilder_AddArgStr("signed", __Pyx_NewRef(Py_True), kwds, args+3, 0) < 0) goto limited_bad;
            }
            result = __Pyx_Object_Vectorcall_CallFromBuilder(from_bytes, args+1, 2 | __Pyx_PY_VECTORCALL_ARGUMENTS_OFFSET, kwds);
        }
        limited_bad:
        Py_XDECREF(kwds);
        Py_XDECREF(order_str);
        Py_XDECREF(py_bytes);
        Py_XDECREF(from_bytes);
        return result;
#endif
    }
}

/* CIntFromPy */
static CYTHON_INLINE long __Pyx_PyLong_As_long(PyObject *x) {
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#endif
    const long neg_one = (long) -1, const_zero = (long) 0;
#ifdef __Pyx_HAS_GCC_DIAGNOSTIC
#pragma GCC diagnostic pop
#endif
    const int is_unsigned = neg_one > const_zero;
    if (unlikely(!PyLong_Check(x))) {
        long val;
        PyObject *tmp = __Pyx_PyNumber_Long(x);
        if (!tmp) return (long) -1;
        val = __Pyx_PyLong_As_long(tmp);
        Py_DECREF(tmp);
        return val;
    }
    if (is_unsigned) {
#if CYTHON_USE_PYLONG_INTERNALS
        if (unlikely(__Pyx_PyLong_IsNeg(x))) {
            goto raise_neg_overflow;
        } else if (__Pyx_PyLong_IsCompact(x)) {
            __PYX_VERIFY_RETURN_INT(long, __Pyx_compact_upylong, __Pyx_PyLong_CompactValueUnsigned(x))
        } else {
            const digit* digits = __Pyx_PyLong_Digits(x);
            assert(__Pyx_PyLong_DigitCount(x) > 1);
            switch (__Pyx_PyLong_DigitCount(x)) {
                case 2:
                    if ((8 * sizeof(long) > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) >= 2 * PyLong_SHIFT)) {
                            return (long) (((((long)digits[1]) << PyLong_SHIFT) | (long)digits[0]));
                        }
                    }
                    break;
                case 3:
                    if ((8 * sizeof(long) > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) >= 3 * PyLong_SHIFT)) {
                            return (long) (((((((long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0]));
                        }
                    }
                    break;
                case 4:
                    if ((8 * sizeof(long) > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) >= 4 * PyLong_SHIFT)) {
                            return (long) (((((((((long)digits[3]) << PyLong_SHIFT) | (long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0]));
                        }
                    }
                    break;
            }
        }
#endif
#if CYTHON_COMPILING_IN_CPYTHON && PY_VERSION_HEX < 0x030C00A7
        if (unlikely(Py_SIZE(x) < 0)) {
            goto raise_neg_overflow;
        }
#else
        {
            int result = PyObject_RichCompareBool(x, Py_False, Py_LT);
            if (unlikely(result < 0))
                return (long) -1;
            if (unlikely(result == 1))
                goto raise_neg_overflow;
        }
#endif
        if ((sizeof(long) <= sizeof(unsigned long))) {
            __PYX_VERIFY_RETURN_INT_EXC(long, unsigned long, PyLong_AsUnsignedLong(x))
#ifdef HAVE_LONG_LONG
        } else if ((sizeof(long) <= sizeof(unsigned PY_LONG_LONG))) {
            __PYX_VERIFY_RETURN_INT_EXC(long, unsigned PY_LONG_LONG, PyLong_AsUnsignedLongLong(x))
#endif
        }
    } else {
#if CYTHON_USE_PYLONG_INTERNALS
        if (__Pyx_PyLong_IsCompact(x)) {
            __PYX_VERIFY_RETURN_INT(long, __Pyx_compact_pylong, __Pyx_PyLong_CompactValue(x))
        } else {
            const digit* digits = __Pyx_PyLong_Digits(x);
            assert(__Pyx_PyLong_DigitCount(x) > 1);
            switch (__Pyx_PyLong_SignedDigitCount(x)) {
                case -2:
                    if ((8 * sizeof(long) - 1 > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, long, -(long) (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 2 * PyLong_SHIFT)) {
                            return (long) (((long)-1)*(((((long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
                case 2:
                    if ((8 * sizeof(long) > 1 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 2 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 2 * PyLong_SHIFT)) {
                            return (long) ((((((long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
                case -3:
                    if ((8 * sizeof(long) - 1 > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, long, -(long) (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 3 * PyLong_SHIFT)) {
                            return (long) (((long)-1)*(((((((long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
                case 3:
                    if ((8 * sizeof(long) > 2 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 3 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((((unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 3 * PyLong_SHIFT)) {
                            return (long) ((((((((long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
                case -4:
                    if ((8 * sizeof(long) - 1 > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, long, -(long) (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 4 * PyLong_SHIFT)) {
                            return (long) (((long)-1)*(((((((((long)digits[3]) << PyLong_SHIFT) | (long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
                case 4:
                    if ((8 * sizeof(long) > 3 * PyLong_SHIFT)) {
                        if ((8 * sizeof(unsigned long) > 4 * PyLong_SHIFT)) {
                            __PYX_VERIFY_RETURN_INT(long, unsigned long, (((((((((unsigned long)digits[3]) << PyLong_SHIFT) | (unsigned long)digits[2]) << PyLong_SHIFT) | (unsigned long)digits[1]) << PyLong_SHIFT) | (unsigned long)digits[0])))
                        } else if ((8 * sizeof(long) - 1 > 4 * PyLong_SHIFT)) {
                            return (long) ((((((((((long)digits[3]) << PyLong_SHIFT) | (long)digits[2]) << PyLong_SHIFT) | (long)digits[1]) << PyLong_SHIFT) | (long)digits[0])));
                        }
                    }
                    break;
            }
        }
#endif
        if ((sizeof(long) <= sizeof(long))) {
            __PYX_VERIFY_RETURN_INT_EXC(long, long, PyLong_AsLong(x))
#ifdef HAVE_LONG_LONG
        } else if ((sizeof(long) <= sizeof(PY_LONG_LONG))) {
            __PYX_VERIFY_RETURN_INT_EXC(long, PY_LONG_LONG, PyLong_AsLongLong(x))
#endif
        }
    }
    {
        long val;
        int ret = -1;
#if PY_VERSION_HEX >= 0x030d00A6 && !CYTHON_COMPILING_IN_LIMITED_API
        Py_ssize_t bytes_copied = PyLong_AsNativeBytes(
            x, &val, sizeof(val), Py_ASNATIVEBYTES_NATIVE_ENDIAN | (is_unsigned ? Py_ASNATIVEBYTES_UNSIGNED_BUFFER | Py_ASNATIVEBYTES_REJECT_NEGATIVE : 0));
        if (unlikely(bytes_copied == -1)) {
        } else if (unlikely(bytes_copied > (Py_ssize_t) sizeof(val))) {
            goto raise_overflow;
        } else {
            ret = 0;
        }
#elif PY_VERSION_HEX < 0x030d0000 && !(CYTHON_COMPILING_IN_PYPY || CYTHON_COMPILING_IN_LIMITED_API) || defined(_PyLong_AsByteArray)
        int one = 1; int is_little = (int)*(unsigned char *)&one;
        unsigned char *bytes = (unsigned char *)&val;
        ret = _PyLong_AsByteArray((PyLongObject *)x,
                                    bytes, sizeof(val),
                                    is_little, !is_unsigned);
#else
        PyObject *v;
        PyObject *stepval = NULL, *mask = NULL, *shift = NULL;
        int bits, remaining_bits, is_negative = 0;
        int chunk_size = (sizeof(long) < 8) ? 30 : 62;
        if (likely(PyLong_CheckExact(x))) {
            v = __Pyx_NewRef(x);
        } else {
            v = PyNumber_Long(x);
            if (unlikely(!v)) return (long) -1;
            assert(PyLong_CheckExact(v));
        }
        {
            int result = PyObject_RichCompareBool(v, Py_False, Py_LT);
            if (unlikely(result < 0)) {
                Py_DECREF(v);
                return (long) -1;
            }
            is_negative = result == 1;
        }
        if (is_unsigned && unlikely(is_negative)) {
            Py_DECREF(v);
            goto raise_neg_overflow;
        } else if (is_negative) {
            stepval = PyNumber_Invert(v);
            Py_DECREF(v);
            if (unlikely(!stepval))
                return (long) -1;
        } else {
            stepval = v;
        }
        v = NULL;
        val = (long) 0;
        mask = PyLong_FromLong((1L << chunk_size) - 1); if (unlikely(!mask)) goto done;
        shift = PyLong_FromLong(chunk_size); if (unlikely(!shift)) goto done;
        for (bits = 0; bits < (int) sizeof(long) * 8 - chunk_size; bits += chunk_size) {
            PyObject *tmp, *digit;
            long idigit;
            digit = PyNumber_And(stepval, mask);
            if (unlikely(!digit)) goto done;
            idigit = PyLong_AsLong(digit);
            Py_DECREF(digit);
            if (unlikely(idigit < 0)) goto done;
            val |= ((long) idigit) << bits;
            tmp = PyNumber_Rshift(stepval, shift);
            if (unlikely(!tmp)) goto done;
            Py_DECREF(stepval); stepval = tmp;
        }
        Py_DECREF(shift); shift = NULL;
        Py_DECREF(mask); mask = NULL;
        {
            long idigit = PyLong_AsLong(stepval);
            if (unlikely(idigit < 0)) goto done;
            remaining_bits = ((int) sizeof(long) * 8) - bits - (is_unsigned ? 0 : 1);
            if (unlikely(idigit >= (1L << remaining_bits)))
                goto raise_overflow;
            val |= ((long) idigit) << bits;
        }
        if (!is_unsigned) {
            if (unlikely(val & (((long) 1) << (sizeof(long) * 8 - 1))))
                goto raise_overflow;
            if (is_negative)
                val = ~val;
        }
        ret = 0;
    done:
        Py_XDECREF(shift);
        Py_XDECREF(mask);
        Py_XDECREF(stepval);
#endif
        if (unlikely(ret))
            return (long) -1;
        return val;
    }
raise_overflow:
    PyErr_SetString(PyExc_OverflowError,
        "value too large to convert to long");
    return (long) -1;
raise_neg_overflow:
    PyErr_SetString(PyExc_OverflowError,
        "can't convert negative value to long");
    return (long) -1;
}

/* FastTypeChecks */
#if CYTHON_COMPILING_IN_CPYTHON
static int __Pyx_InBases(PyTypeObject *a, PyTypeObject *b) {
    while (a) {
        a = __Pyx_PyType_GetSlot(a, tp_base, PyTypeObject*);
        if (a == b)
            return 1;
    }
    return b == &PyBaseObject_Type;
}
static CYTHON_INLINE int __Pyx_IsSubtype(PyTypeObject *a, PyTypeObject *b) {
    PyObject *mro;
    if (a == b) return 1;
    mro = a->tp_mro;
    if (likely(mro)) {
        Py_ssize_t i, n;
        n = PyTuple_GET_SIZE(mro);
        for (i = 0; i < n; i++) {
            if (PyTuple_GET_ITEM(mro, i) == (PyObject *)b)
                return 1;
        }
        return 0;
    }
    return __Pyx_InBases(a, b);
}
static CYTHON_INLINE int __Pyx_IsAnySubtype2(PyTypeObject *cls, PyTypeObject *a, PyTypeObject *b) {
    PyObject *mro;
    if (cls == a || cls == b) return 1;
    mro = cls->tp_mro;
    if (likely(mro)) {
        Py_ssize_t i, n;
        n = PyTuple_GET_SIZE(mro);
        for (i = 0; i < n; i++) {
            PyObject *base = PyTuple_GET_ITEM(mro, i);
            if (base == (PyObject *)a || base == (PyObject *)b)
                return 1;
        }
        return 0;
    }
    return __Pyx_InBases(cls, a) || __Pyx_InBases(cls, b);
}
static CYTHON_INLINE int __Pyx_inner_PyErr_GivenExceptionMatches2(PyObject *err, PyObject* exc_type1, PyObject *exc_type2) {
    if (exc_type1) {
        return __Pyx_IsAnySubtype2((PyTypeObject*)err, (PyTypeObject*)exc_type1, (PyTypeObject*)exc_type2);
    } else {
        return __Pyx_IsSubtype((PyTypeObject*)err, (PyTypeObject*)exc_type2);
    }
}
static int __Pyx_PyErr_GivenExceptionMatchesTuple(PyObject *exc_type, PyObject *tuple) {
    Py_ssize_t i, n;
    assert(PyExceptionClass_Check(exc_type));
    n = PyTuple_GET_SIZE(tuple);
    for (i=0; i<n; i++) {
        if (exc_type == PyTuple_GET_ITEM(tuple, i)) return 1;
    }
    for (i=0; i<n; i++) {
        PyObject *t = PyTuple_GET_ITEM(tuple, i);
        if (likely(PyExceptionClass_Check(t))) {
            if (__Pyx_inner_PyErr_GivenExceptionMatches2(exc_type, NULL, t)) return 1;
        } else {
        }
    }
    return 0;
}
static CYTHON_INLINE int __Pyx_PyErr_GivenExceptionMatches(PyObject *err, PyObject* exc_type) {
    if (likely(err == exc_type)) return 1;
    if (likely(PyExceptionClass_Check(err))) {
        if (likely(PyExceptionClass_Check(exc_type))) {
            return __Pyx_inner_PyErr_GivenExceptionMatches2(err, NULL, exc_type);
        } else if (likely(PyTuple_Check(exc_type))) {
            return __Pyx_PyErr_GivenExceptionMatchesTuple(err, exc_type);
        } else {
        }
    }
    return PyErr_GivenExceptionMatches(err, exc_type);
}
static CYTHON_INLINE int __Pyx_PyErr_GivenExceptionMatches2(PyObject *err, PyObject *exc_type1, PyObject *exc_type2) {
    assert(PyExceptionClass_Check(exc_type1));
    assert(PyExceptionClass_Check(exc_type2));
    if (likely(err == exc_type1 || err == exc_type2)) return 1;
    if (likely(PyExceptionClass_Check(err))) {
        return __Pyx_inner_PyErr_GivenExceptionMatches2(err, exc_type1, exc_type2);
    }
    return (PyErr_GivenExceptionMatches(err, exc_type1) || PyErr_GivenExceptionMatches(err, exc_type2));
}
#endif

/* GetRuntimeVersion */
static unsigned long __Pyx_get_runtime_version(void) {
#if __PYX_LIMITED_VERSION_HEX >= 0x030b0000
    return Py_Version & ~0xFFUL;
#else
    static unsigned long __Pyx_cached_runtime_version = 0;
    if (__Pyx_cached_runtime_version == 0) {
        const char* rt_version = Py_GetVersion();
        unsigned long version = 0;
        unsigned long factor = 0x01000000UL;
        unsigned int digit = 0;
        int i = 0;
        while (factor) {
            while ('0' <= rt_version[i] && rt_version[i] <= '9') {
                digit = digit * 10 + (unsigned int) (rt_version[i] - '0');
                ++i;
            }
            version += factor * digit;
            if (rt_version[i] != '.')
                break;
            digit = 0;
            factor >>= 8;
            ++i;
        }
        __Pyx_cached_runtime_version = version;
    }
    return __Pyx_cached_runtime_version;
#endif
}

/* CheckBinaryVersion */
static int __Pyx_check_binary_version(unsigned long ct_version, unsigned long rt_version, int allow_newer) {
    const unsigned long MAJOR_MINOR = 0xFFFF0000UL;
    if ((rt_version & MAJOR_MINOR) == (ct_version & MAJOR_MINOR))
        return 0;
    if (likely(allow_newer && (rt_version & MAJOR_MINOR) > (ct_version & MAJOR_MINOR)))
        return 1;
    {
        char message[200];
        PyOS_snprintf(message, sizeof(message),
                      "compile time Python version %d.%d "
                      "of module '%.100s' "
                      "%s "
                      "runtime version %d.%d",
                       (int) (ct_version >> 24), (int) ((ct_version >> 16) & 0xFF),
                       __Pyx_MODULE_NAME,
                       (allow_newer) ? "was newer than" : "does not match",
                       (int) (rt_version >> 24), (int) ((rt_version >> 16) & 0xFF)
       );
        return PyErr_WarnEx(NULL, message, 1);
    }
}

/* NewCodeObj */
#if CYTHON_COMPILING_IN_LIMITED_API
    static PyObject* __Pyx__PyCode_New(int a, int p, int k, int l, int s, int f,
                                       PyObject *code, PyObject *c, PyObject* n, PyObject *v,
                                       PyObject *fv, PyObject *cell, PyObject* fn,
                                       PyObject *name, int fline, PyObject *lnos) {
        PyObject *exception_table = NULL;
        PyObject *types_module=NULL, *code_type=NULL, *result=NULL;
        #if __PYX_LIMITED_VERSION_HEX < 0x030b0000
        PyObject *version_info;
        PyObject *py_minor_version = NULL;
        #endif
        long minor_version = 0;
        PyObject *type, *value, *traceback;
        PyErr_Fetch(&type, &value, &traceback);
        #if __PYX_LIMITED_VERSION_HEX >= 0x030b0000
        minor_version = 11;
        #else
        if (!(version_info = PySys_GetObject("version_info"))) goto end;
        if (!(py_minor_version = PySequence_GetItem(version_info, 1))) goto end;
        minor_version = PyLong_AsLong(py_minor_version);
        Py_DECREF(py_minor_version);
        if (minor_version == -1 && PyErr_Occurred()) goto end;
        #endif
        if (!(types_module = PyImport_ImportModule("types"))) goto end;
        if (!(code_type = PyObject_GetAttrString(types_module, "CodeType"))) goto end;
        if (minor_version <= 7) {
            (void)p;
            result = PyObject_CallFunction(code_type, "iiiiiOOOOOOiOOO", a, k, l, s, f, code,
                          c, n, v, fn, name, fline, lnos, fv, cell);
        } else if (minor_version <= 10) {
            result = PyObject_CallFunction(code_type, "iiiiiiOOOOOOiOOO", a,p, k, l, s, f, code,
                          c, n, v, fn, name, fline, lnos, fv, cell);
        } else {
            if (!(exception_table = PyBytes_FromStringAndSize(NULL, 0))) goto end;
            result = PyObject_CallFunction(code_type, "iiiiiiOOOOOOOiOOOO", a,p, k, l, s, f, code,
                          c, n, v, fn, name, name, fline, lnos, exception_table, fv, cell);
        }
    end:
        Py_XDECREF(code_type);
        Py_XDECREF(exception_table);
        Py_XDECREF(types_module);
        if (type) {
            PyErr_Restore(type, value, traceback);
        }
        return result;
    }
#elif PY_VERSION_HEX >= 0x030B0000
  static PyCodeObject* __Pyx__PyCode_New(int a, int p, int k, int l, int s, int f,
                                         PyObject *code, PyObject *c, PyObject* n, PyObject *v,
                                         PyObject *fv, PyObject *cell, PyObject* fn,
                                         PyObject *name, int fline, PyObject *lnos) {
    PyCodeObject *result;
    result =
      #if PY_VERSION_HEX >= 0x030C0000
        PyUnstable_Code_NewWithPosOnlyArgs
      #else
        PyCode_NewWithPosOnlyArgs
      #endif
        (a, p, k, l, s, f, code, c, n, v, fv, cell, fn, name, name, fline, lnos, __pyx_mstate_global->__pyx_empty_bytes);
    return result;
  }
#elif PY_VERSION_HEX >= 0x030800B2 && !CYTHON_COMPILING_IN_PYPY
  #define __Pyx__PyCode_New(a, p, k, l, s, f, code, c, n, v, fv, cell, fn, name, fline, lnos)\
          PyCode_NewWithPosOnlyArgs(a, p, k, l, s, f, code, c, n, v, fv, cell, fn, name, fline, lnos)
#else
  #define __Pyx__PyCode_New(a, p, k, l, s, f, code, c, n, v, fv, cell, fn, name, fline, lnos)\
          PyCode_New(a, k, l, s, f, code, c, n, v, fv, cell, fn, name, fline, lnos)
#endif
static PyObject* __Pyx_PyCode_New(
        const __Pyx_PyCode_New_function_description descr,
        PyObject * const *varnames,
        PyObject *filename,
        PyObject *funcname,
        const char *line_table,
        PyObject *tuple_dedup_map
) {
    PyObject *code_obj = NULL, *varnames_tuple_dedup = NULL, *code_bytes = NULL, *line_table_bytes = NULL;
    Py_ssize_t var_count = (Py_ssize_t) descr.nlocals;
    PyObject *varnames_tuple = PyTuple_New(var_count);
    if (unlikely(!varnames_tuple)) return NULL;
    for (Py_ssize_t i=0; i < var_count; i++) {
        Py_INCREF(varnames[i]);
        if (__Pyx_PyTuple_SET_ITEM(varnames_tuple, i, varnames[i]) != (0)) goto done;
    }
    #if CYTHON_COMPILING_IN_LIMITED_API
    varnames_tuple_dedup = PyDict_GetItem(tuple_dedup_map, varnames_tuple);
    if (!varnames_tuple_dedup) {
        if (unlikely(PyDict_SetItem(tuple_dedup_map, varnames_tuple, varnames_tuple) < 0)) goto done;
        varnames_tuple_dedup = varnames_tuple;
    }
    #else
    varnames_tuple_dedup = PyDict_SetDefault(tuple_dedup_map, varnames_tuple, varnames_tuple);
    if (unlikely(!varnames_tuple_dedup)) goto done;
    #endif
    #if CYTHON_AVOID_BORROWED_REFS
    Py_INCREF(varnames_tuple_dedup);
    #endif
    if (__PYX_LIMITED_VERSION_HEX >= (0x030b0000) && line_table != NULL
        && !CYTHON_COMPILING_IN_GRAAL) {
        line_table_bytes = PyBytes_FromStringAndSize(line_table, descr.line_table_length);
        if (unlikely(!line_table_bytes)) goto done;
        Py_ssize_t code_len = (descr.line_table_length * 2 + 4) & ~3;
        code_bytes = PyBytes_FromStringAndSize(NULL, code_len);
        if (unlikely(!code_bytes)) goto done;
        char* c_code_bytes = PyBytes_AsString(code_bytes);
        if (unlikely(!c_code_bytes)) goto done;
        memset(c_code_bytes, 0, (size_t) code_len);
    }
    code_obj = (PyObject*) __Pyx__PyCode_New(
        (int) descr.argcount,
        (int) descr.num_posonly_args,
        (int) descr.num_kwonly_args,
        (int) descr.nlocals,
        0,
        (int) descr.flags,
        code_bytes ? code_bytes : __pyx_mstate_global->__pyx_empty_bytes,
        __pyx_mstate_global->__pyx_empty_tuple,
        __pyx_mstate_global->__pyx_empty_tuple,
        varnames_tuple_dedup,
        __pyx_mstate_global->__pyx_empty_tuple,
        __pyx_mstate_global->__pyx_empty_tuple,
        filename,
        funcname,
        (int) descr.first_line,
        (__PYX_LIMITED_VERSION_HEX >= (0x030b0000) && line_table_bytes) ? line_table_bytes : __pyx_mstate_global->__pyx_empty_bytes
    );
done:
    Py_XDECREF(code_bytes);
    Py_XDECREF(line_table_bytes);
    #if CYTHON_AVOID_BORROWED_REFS
    Py_XDECREF(varnames_tuple_dedup);
    #endif
    Py_DECREF(varnames_tuple);
    return code_obj;
}

/* InitStrings */
static int __Pyx_InitStrings(__Pyx_StringTabEntry const *t, PyObject **target, const char* const* encoding_names) {
    while (t->s) {
        PyObject *str;
        if (t->is_unicode) {
            if (t->intern) {
                str = PyUnicode_InternFromString(t->s);
            } else if (t->encoding) {
                str = PyUnicode_Decode(t->s, t->n - 1, encoding_names[t->encoding], NULL);
            } else {
                str = PyUnicode_FromStringAndSize(t->s, t->n - 1);
            }
        } else {
            str = PyBytes_FromStringAndSize(t->s, t->n - 1);
        }
        if (!str)
            return -1;
        *target = str;
        if (PyObject_Hash(str) == -1)
            return -1;
        ++t;
        ++target;
    }
    return 0;
}

#include <string.h>
static CYTHON_INLINE Py_ssize_t __Pyx_ssize_strlen(const char *s) {
    size_t len = strlen(s);
    if (unlikely(len > (size_t) PY_SSIZE_T_MAX)) {
        PyErr_SetString(PyExc_OverflowError, "byte string is too long");
        return -1;
    }
    return (Py_ssize_t) len;
}
static CYTHON_INLINE PyObject* __Pyx_PyUnicode_FromString(const char* c_str) {
    Py_ssize_t len = __Pyx_ssize_strlen(c_str);
    if (unlikely(len < 0)) return NULL;
    return __Pyx_PyUnicode_FromStringAndSize(c_str, len);
}
static CYTHON_INLINE PyObject* __Pyx_PyByteArray_FromString(const char* c_str) {
    Py_ssize_t len = __Pyx_ssize_strlen(c_str);
    if (unlikely(len < 0)) return NULL;
    return PyByteArray_FromStringAndSize(c_str, len);
}
static CYTHON_INLINE const char* __Pyx_PyObject_AsString(PyObject* o) {
    Py_ssize_t ignore;
    return __Pyx_PyObject_AsStringAndSize(o, &ignore);
}
#if __PYX_DEFAULT_STRING_ENCODING_IS_ASCII || __PYX_DEFAULT_STRING_ENCODING_IS_UTF8
static CYTHON_INLINE const char* __Pyx_PyUnicode_AsStringAndSize(PyObject* o, Py_ssize_t *length) {
    if (unlikely(__Pyx_PyUnicode_READY(o) == -1)) return NULL;
#if CYTHON_COMPILING_IN_LIMITED_API
    {
        const char* result;
        Py_ssize_t unicode_length;
        CYTHON_MAYBE_UNUSED_VAR(unicode_length); // only for __PYX_DEFAULT_STRING_ENCODING_IS_ASCII
        #if __PYX_LIMITED_VERSION_HEX < 0x030A0000
        if (unlikely(PyArg_Parse(o, "s#", &result, length) < 0)) return NULL;
        #else
        result = PyUnicode_AsUTF8AndSize(o, length);
        #endif
        #if __PYX_DEFAULT_STRING_ENCODING_IS_ASCII
        unicode_length = PyUnicode_GetLength(o);
        if (unlikely(unicode_length < 0)) return NULL;
        if (unlikely(unicode_length != *length)) {
            PyUnicode_AsASCIIString(o);
            return NULL;
        }
        #endif
        return result;
    }
#else
#if __PYX_DEFAULT_STRING_ENCODING_IS_ASCII
    if (likely(PyUnicode_IS_ASCII(o))) {
        *length = PyUnicode_GET_LENGTH(o);
        return PyUnicode_AsUTF8(o);
    } else {
        PyUnicode_AsASCIIString(o);
        return NULL;
    }
#else
    return PyUnicode_AsUTF8AndSize(o, length);
#endif
#endif
}
#endif
static CYTHON_INLINE const char* __Pyx_PyObject_AsStringAndSize(PyObject* o, Py_ssize_t *length) {
#if __PYX_DEFAULT_STRING_ENCODING_IS_ASCII || __PYX_DEFAULT_STRING_ENCODING_IS_UTF8
    if (PyUnicode_Check(o)) {
        return __Pyx_PyUnicode_AsStringAndSize(o, length);
    } else
#endif
    if (PyByteArray_Check(o)) {
#if (CYTHON_ASSUME_SAFE_SIZE && CYTHON_ASSUME_SAFE_MACROS) || (CYTHON_COMPILING_IN_PYPY && (defined(PyByteArray_AS_STRING) && defined(PyByteArray_GET_SIZE)))
        *length = PyByteArray_GET_SIZE(o);
        return PyByteArray_AS_STRING(o);
#else
        *length = PyByteArray_Size(o);
        if (*length == -1) return NULL;
        return PyByteArray_AsString(o);
#endif
    } else
    {
        char* result;
        int r = PyBytes_AsStringAndSize(o, &result, length);
        if (unlikely(r < 0)) {
            return NULL;
        } else {
            return result;
        }
    }
}
static CYTHON_INLINE int __Pyx_PyObject_IsTrue(PyObject* x) {
   int is_true = x == Py_True;
   if (is_true | (x == Py_False) | (x == Py_None)) return is_true;
   else return PyObject_IsTrue(x);
}
static CYTHON_INLINE int __Pyx_PyObject_IsTrueAndDecref(PyObject* x) {
    int retval;
    if (unlikely(!x)) return -1;
    retval = __Pyx_PyObject_IsTrue(x);
    Py_DECREF(x);
    return retval;
}
static PyObject* __Pyx_PyNumber_LongWrongResultType(PyObject* result) {
    __Pyx_TypeName result_type_name = __Pyx_PyType_GetFullyQualifiedName(Py_TYPE(result));
    if (PyLong_Check(result)) {
        if (PyErr_WarnFormat(PyExc_DeprecationWarning, 1,
                "__int__ returned non-int (type " __Pyx_FMT_TYPENAME ").  "
                "The ability to return an instance of a strict subclass of int is deprecated, "
                "and may be removed in a future version of Python.",
                result_type_name)) {
            __Pyx_DECREF_TypeName(result_type_name);
            Py_DECREF(result);
            return NULL;
        }
        __Pyx_DECREF_TypeName(result_type_name);
        return result;
    }
    PyErr_Format(PyExc_TypeError,
                 "__int__ returned non-int (type " __Pyx_FMT_TYPENAME ")",
                 result_type_name);
    __Pyx_DECREF_TypeName(result_type_name);
    Py_DECREF(result);
    return NULL;
}
static CYTHON_INLINE PyObject* __Pyx_PyNumber_Long(PyObject* x) {
#if CYTHON_USE_TYPE_SLOTS
  PyNumberMethods *m;
#endif
  PyObject *res = NULL;
  if (likely(PyLong_Check(x)))
      return __Pyx_NewRef(x);
#if CYTHON_USE_TYPE_SLOTS
  m = Py_TYPE(x)->tp_as_number;
  if (likely(m && m->nb_int)) {
      res = m->nb_int(x);
  }
#else
  if (!PyBytes_CheckExact(x) && !PyUnicode_CheckExact(x)) {
      res = PyNumber_Long(x);
  }
#endif
  if (likely(res)) {
      if (unlikely(!PyLong_CheckExact(res))) {
          return __Pyx_PyNumber_LongWrongResultType(res);
      }
  }
  else if (!PyErr_Occurred()) {
      PyErr_SetString(PyExc_TypeError,
                      "an integer is required");
  }
  return res;
}
static CYTHON_INLINE Py_ssize_t __Pyx_PyIndex_AsSsize_t(PyObject* b) {
  Py_ssize_t ival;
  PyObject *x;
  if (likely(PyLong_CheckExact(b))) {
    #if CYTHON_USE_PYLONG_INTERNALS
    if (likely(__Pyx_PyLong_IsCompact(b))) {
        return __Pyx_PyLong_CompactValue(b);
    } else {
      const digit* digits = __Pyx_PyLong_Digits(b);
      const Py_ssize_t size = __Pyx_PyLong_SignedDigitCount(b);
      switch (size) {
         case 2:
           if (8 * sizeof(Py_ssize_t) > 2 * PyLong_SHIFT) {
             return (Py_ssize_t) (((((size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
         case -2:
           if (8 * sizeof(Py_ssize_t) > 2 * PyLong_SHIFT) {
             return -(Py_ssize_t) (((((size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
         case 3:
           if (8 * sizeof(Py_ssize_t) > 3 * PyLong_SHIFT) {
             return (Py_ssize_t) (((((((size_t)digits[2]) << PyLong_SHIFT) | (size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
         case -3:
           if (8 * sizeof(Py_ssize_t) > 3 * PyLong_SHIFT) {
             return -(Py_ssize_t) (((((((size_t)digits[2]) << PyLong_SHIFT) | (size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
         case 4:
           if (8 * sizeof(Py_ssize_t) > 4 * PyLong_SHIFT) {
             return (Py_ssize_t) (((((((((size_t)digits[3]) << PyLong_SHIFT) | (size_t)digits[2]) << PyLong_SHIFT) | (size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
         case -4:
           if (8 * sizeof(Py_ssize_t) > 4 * PyLong_SHIFT) {
             return -(Py_ssize_t) (((((((((size_t)digits[3]) << PyLong_SHIFT) | (size_t)digits[2]) << PyLong_SHIFT) | (size_t)digits[1]) << PyLong_SHIFT) | (size_t)digits[0]));
           }
           break;
      }
    }
    #endif
    return PyLong_AsSsize_t(b);
  }
  x = PyNumber_Index(b);
  if (!x) return -1;
  ival = PyLong_AsSsize_t(x);
  Py_DECREF(x);
  return ival;
}
static CYTHON_INLINE Py_hash_t __Pyx_PyIndex_AsHash_t(PyObject* o) {
  if (sizeof(Py_hash_t) == sizeof(Py_ssize_t)) {
    return (Py_hash_t) __Pyx_PyIndex_AsSsize_t(o);
  } else {
    Py_ssize_t ival;
    PyObject *x;
    x = PyNumber_Index(o);
    if (!x) return -1;
    ival = PyLong_AsLong(x);
    Py_DECREF(x);
    return ival;
  }
}
static CYTHON_INLINE PyObject *__Pyx_Owned_Py_None(int b) {
    CYTHON_UNUSED_VAR(b);
    return __Pyx_NewRef(Py_None);
}
static CYTHON_INLINE PyObject * __Pyx_PyBool_FromLong(long b) {
  return b ? __Pyx_NewRef(Py_True) : __Pyx_NewRef(Py_False);
}
static CYTHON_INLINE PyObject * __Pyx_PyLong_FromSize_t(size_t ival) {
    return PyLong_FromSize_t(ival);
}


/* MultiPhaseInitModuleState */
#if CYTHON_PEP489_MULTI_PHASE_INIT && CYTHON_USE_MODULE_STATE
#ifndef CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
#if (CYTHON_COMPILING_IN_LIMITED_API || PY_VERSION_HEX >= 0x030C0000)
  #define CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE 1
#else
  #define CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE 0
#endif
#endif
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE && !CYTHON_ATOMICS
#error "Module state with PEP489 requires atomics. Currently that's one of\
 C11, C++11, gcc atomic intrinsics or MSVC atomic intrinsics"
#endif
#if !CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
#define __Pyx_ModuleStateLookup_Lock()
#define __Pyx_ModuleStateLookup_Unlock()
#elif !CYTHON_COMPILING_IN_LIMITED_API && PY_VERSION_HEX >= 0x030d0000
static PyMutex __Pyx_ModuleStateLookup_mutex = {0};
#define __Pyx_ModuleStateLookup_Lock() PyMutex_Lock(&__Pyx_ModuleStateLookup_mutex)
#define __Pyx_ModuleStateLookup_Unlock() PyMutex_Unlock(&__Pyx_ModuleStateLookup_mutex)
#elif defined(__cplusplus) && __cplusplus >= 201103L
#include <mutex>
static std::mutex __Pyx_ModuleStateLookup_mutex;
#define __Pyx_ModuleStateLookup_Lock() __Pyx_ModuleStateLookup_mutex.lock()
#define __Pyx_ModuleStateLookup_Unlock() __Pyx_ModuleStateLookup_mutex.unlock()
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ > 201112L) && !defined(__STDC_NO_THREADS__)
#include <threads.h>
static mtx_t __Pyx_ModuleStateLookup_mutex;
static once_flag __Pyx_ModuleStateLookup_mutex_once_flag = ONCE_FLAG_INIT;
static void __Pyx_ModuleStateLookup_initialize_mutex(void) {
    mtx_init(&__Pyx_ModuleStateLookup_mutex, mtx_plain);
}
#define __Pyx_ModuleStateLookup_Lock()\
  call_once(&__Pyx_ModuleStateLookup_mutex_once_flag, __Pyx_ModuleStateLookup_initialize_mutex);\
  mtx_lock(&__Pyx_ModuleStateLookup_mutex)
#define __Pyx_ModuleStateLookup_Unlock() mtx_unlock(&__Pyx_ModuleStateLookup_mutex)
#elif defined(HAVE_PTHREAD_H)
#include <pthread.h>
static pthread_mutex_t __Pyx_ModuleStateLookup_mutex = PTHREAD_MUTEX_INITIALIZER;
#define __Pyx_ModuleStateLookup_Lock() pthread_mutex_lock(&__Pyx_ModuleStateLookup_mutex)
#define __Pyx_ModuleStateLookup_Unlock() pthread_mutex_unlock(&__Pyx_ModuleStateLookup_mutex)
#elif defined(_WIN32)
#include <Windows.h>  // synchapi.h on its own doesn't work
static SRWLOCK __Pyx_ModuleStateLookup_mutex = SRWLOCK_INIT;
#define __Pyx_ModuleStateLookup_Lock() AcquireSRWLockExclusive(&__Pyx_ModuleStateLookup_mutex)
#define __Pyx_ModuleStateLookup_Unlock() ReleaseSRWLockExclusive(&__Pyx_ModuleStateLookup_mutex)
#else
#error "No suitable lock available for CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE.\
 Requires C standard >= C11, or C++ standard >= C++11,\
 or pthreads, or the Windows 32 API, or Python >= 3.13."
#endif
typedef struct {
    int64_t id;
    PyObject *module;
} __Pyx_InterpreterIdAndModule;
typedef struct {
    char interpreter_id_as_index;
    Py_ssize_t count;
    Py_ssize_t allocated;
    __Pyx_InterpreterIdAndModule table[1];
} __Pyx_ModuleStateLookupData;
#define __PYX_MODULE_STATE_LOOKUP_SMALL_SIZE 32
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
static __pyx_atomic_int_type __Pyx_ModuleStateLookup_read_counter = 0;
#endif
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
static __pyx_atomic_ptr_type __Pyx_ModuleStateLookup_data = 0;
#else
static __Pyx_ModuleStateLookupData* __Pyx_ModuleStateLookup_data = NULL;
#endif
static __Pyx_InterpreterIdAndModule* __Pyx_State_FindModuleStateLookupTableLowerBound(
        __Pyx_InterpreterIdAndModule* table,
        Py_ssize_t count,
        int64_t interpreterId) {
    __Pyx_InterpreterIdAndModule* begin = table;
    __Pyx_InterpreterIdAndModule* end = begin + count;
    if (begin->id == interpreterId) {
        return begin;
    }
    while ((end - begin) > __PYX_MODULE_STATE_LOOKUP_SMALL_SIZE) {
        __Pyx_InterpreterIdAndModule* halfway = begin + (end - begin)/2;
        if (halfway->id == interpreterId) {
            return halfway;
        }
        if (halfway->id < interpreterId) {
            begin = halfway;
        } else {
            end = halfway;
        }
    }
    for (; begin < end; ++begin) {
        if (begin->id >= interpreterId) return begin;
    }
    return begin;
}
static PyObject *__Pyx_State_FindModule(CYTHON_UNUSED void* dummy) {
    int64_t interpreter_id = PyInterpreterState_GetID(__Pyx_PyInterpreterState_Get());
    if (interpreter_id == -1) return NULL;
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
    __Pyx_ModuleStateLookupData* data = (__Pyx_ModuleStateLookupData*)__pyx_atomic_pointer_load_relaxed(&__Pyx_ModuleStateLookup_data);
    {
        __pyx_atomic_incr_acq_rel(&__Pyx_ModuleStateLookup_read_counter);
        if (likely(data)) {
            __Pyx_ModuleStateLookupData* new_data = (__Pyx_ModuleStateLookupData*)__pyx_atomic_pointer_load_acquire(&__Pyx_ModuleStateLookup_data);
            if (likely(data == new_data)) {
                goto read_finished;
            }
        }
        __pyx_atomic_decr_acq_rel(&__Pyx_ModuleStateLookup_read_counter);
        __Pyx_ModuleStateLookup_Lock();
        __pyx_atomic_incr_relaxed(&__Pyx_ModuleStateLookup_read_counter);
        data = (__Pyx_ModuleStateLookupData*)__pyx_atomic_pointer_load_relaxed(&__Pyx_ModuleStateLookup_data);
        __Pyx_ModuleStateLookup_Unlock();
    }
  read_finished:;
#else
    __Pyx_ModuleStateLookupData* data = __Pyx_ModuleStateLookup_data;
#endif
    __Pyx_InterpreterIdAndModule* found = NULL;
    if (unlikely(!data)) goto end;
    if (data->interpreter_id_as_index) {
        if (interpreter_id < data->count) {
            found = data->table+interpreter_id;
        }
    } else {
        found = __Pyx_State_FindModuleStateLookupTableLowerBound(
            data->table, data->count, interpreter_id);
    }
  end:
    {
        PyObject *result=NULL;
        if (found && found->id == interpreter_id) {
            result = found->module;
        }
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
        __pyx_atomic_decr_acq_rel(&__Pyx_ModuleStateLookup_read_counter);
#endif
        return result;
    }
}
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
static void __Pyx_ModuleStateLookup_wait_until_no_readers(void) {
    while (__pyx_atomic_load(&__Pyx_ModuleStateLookup_read_counter) != 0);
}
#else
#define __Pyx_ModuleStateLookup_wait_until_no_readers()
#endif
static int __Pyx_State_AddModuleInterpIdAsIndex(__Pyx_ModuleStateLookupData **old_data, PyObject* module, int64_t interpreter_id) {
    Py_ssize_t to_allocate = (*old_data)->allocated;
    while (to_allocate <= interpreter_id) {
        if (to_allocate == 0) to_allocate = 1;
        else to_allocate *= 2;
    }
    __Pyx_ModuleStateLookupData *new_data = *old_data;
    if (to_allocate != (*old_data)->allocated) {
         new_data = (__Pyx_ModuleStateLookupData *)realloc(
            *old_data,
            sizeof(__Pyx_ModuleStateLookupData)+(to_allocate-1)*sizeof(__Pyx_InterpreterIdAndModule));
        if (!new_data) {
            PyErr_NoMemory();
            return -1;
        }
        for (Py_ssize_t i = new_data->allocated; i < to_allocate; ++i) {
            new_data->table[i].id = i;
            new_data->table[i].module = NULL;
        }
        new_data->allocated = to_allocate;
    }
    new_data->table[interpreter_id].module = module;
    if (new_data->count < interpreter_id+1) {
        new_data->count = interpreter_id+1;
    }
    *old_data = new_data;
    return 0;
}
static void __Pyx_State_ConvertFromInterpIdAsIndex(__Pyx_ModuleStateLookupData *data) {
    __Pyx_InterpreterIdAndModule *read = data->table;
    __Pyx_InterpreterIdAndModule *write = data->table;
    __Pyx_InterpreterIdAndModule *end = read + data->count;
    for (; read<end; ++read) {
        if (read->module) {
            write->id = read->id;
            write->module = read->module;
            ++write;
        }
    }
    data->count = write - data->table;
    for (; write<end; ++write) {
        write->id = 0;
        write->module = NULL;
    }
    data->interpreter_id_as_index = 0;
}
static int __Pyx_State_AddModule(PyObject* module, CYTHON_UNUSED void* dummy) {
    int64_t interpreter_id = PyInterpreterState_GetID(__Pyx_PyInterpreterState_Get());
    if (interpreter_id == -1) return -1;
    int result = 0;
    __Pyx_ModuleStateLookup_Lock();
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
    __Pyx_ModuleStateLookupData *old_data = (__Pyx_ModuleStateLookupData *)
            __pyx_atomic_pointer_exchange(&__Pyx_ModuleStateLookup_data, 0);
#else
    __Pyx_ModuleStateLookupData *old_data = __Pyx_ModuleStateLookup_data;
#endif
    __Pyx_ModuleStateLookupData *new_data = old_data;
    if (!new_data) {
        new_data = (__Pyx_ModuleStateLookupData *)calloc(1, sizeof(__Pyx_ModuleStateLookupData));
        if (!new_data) {
            result = -1;
            PyErr_NoMemory();
            goto end;
        }
        new_data->allocated = 1;
        new_data->interpreter_id_as_index = 1;
    }
    __Pyx_ModuleStateLookup_wait_until_no_readers();
    if (new_data->interpreter_id_as_index) {
        if (interpreter_id < __PYX_MODULE_STATE_LOOKUP_SMALL_SIZE) {
            result = __Pyx_State_AddModuleInterpIdAsIndex(&new_data, module, interpreter_id);
            goto end;
        }
        __Pyx_State_ConvertFromInterpIdAsIndex(new_data);
    }
    {
        Py_ssize_t insert_at = 0;
        {
            __Pyx_InterpreterIdAndModule* lower_bound = __Pyx_State_FindModuleStateLookupTableLowerBound(
                new_data->table, new_data->count, interpreter_id);
            assert(lower_bound);
            insert_at = lower_bound - new_data->table;
            if (unlikely(insert_at < new_data->count && lower_bound->id == interpreter_id)) {
                lower_bound->module = module;
                goto end;  // already in table, nothing more to do
            }
        }
        if (new_data->count+1 >= new_data->allocated) {
            Py_ssize_t to_allocate = (new_data->count+1)*2;
            new_data =
                (__Pyx_ModuleStateLookupData*)realloc(
                    new_data,
                    sizeof(__Pyx_ModuleStateLookupData) +
                    (to_allocate-1)*sizeof(__Pyx_InterpreterIdAndModule));
            if (!new_data) {
                result = -1;
                new_data = old_data;
                PyErr_NoMemory();
                goto end;
            }
            new_data->allocated = to_allocate;
        }
        ++new_data->count;
        int64_t last_id = interpreter_id;
        PyObject *last_module = module;
        for (Py_ssize_t i=insert_at; i<new_data->count; ++i) {
            int64_t current_id = new_data->table[i].id;
            new_data->table[i].id = last_id;
            last_id = current_id;
            PyObject *current_module = new_data->table[i].module;
            new_data->table[i].module = last_module;
            last_module = current_module;
        }
    }
  end:
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
    __pyx_atomic_pointer_exchange(&__Pyx_ModuleStateLookup_data, new_data);
#else
    __Pyx_ModuleStateLookup_data = new_data;
#endif
    __Pyx_ModuleStateLookup_Unlock();
    return result;
}
static int __Pyx_State_RemoveModule(CYTHON_UNUSED void* dummy) {
    int64_t interpreter_id = PyInterpreterState_GetID(__Pyx_PyInterpreterState_Get());
    if (interpreter_id == -1) return -1;
    __Pyx_ModuleStateLookup_Lock();
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
    __Pyx_ModuleStateLookupData *data = (__Pyx_ModuleStateLookupData *)
            __pyx_atomic_pointer_exchange(&__Pyx_ModuleStateLookup_data, 0);
#else
    __Pyx_ModuleStateLookupData *data = __Pyx_ModuleStateLookup_data;
#endif
    if (data->interpreter_id_as_index) {
        if (interpreter_id < data->count) {
            data->table[interpreter_id].module = NULL;
        }
        goto done;
    }
    {
        __Pyx_ModuleStateLookup_wait_until_no_readers();
        __Pyx_InterpreterIdAndModule* lower_bound = __Pyx_State_FindModuleStateLookupTableLowerBound(
            data->table, data->count, interpreter_id);
        if (!lower_bound) goto done;
        if (lower_bound->id != interpreter_id) goto done;
        __Pyx_InterpreterIdAndModule *end = data->table+data->count;
        for (;lower_bound<end-1; ++lower_bound) {
            lower_bound->id = (lower_bound+1)->id;
            lower_bound->module = (lower_bound+1)->module;
        }
    }
    --data->count;
    if (data->count == 0) {
        free(data);
        data = NULL;
    }
  done:
#if CYTHON_MODULE_STATE_LOOKUP_THREAD_SAFE
    __pyx_atomic_pointer_exchange(&__Pyx_ModuleStateLookup_data, data);
#else
    __Pyx_ModuleStateLookup_data = data;
#endif
    __Pyx_ModuleStateLookup_Unlock();
    return 0;
}
#endif

/* #### Code section: utility_code_pragmas_end ### */
#ifdef _MSC_VER
#pragma warning( pop )
#endif



/* #### Code section: end ### */
#endif /* Py_PYTHON_H */
EOF

cat > /workspace/solver_c.pyx << 'EOF'
# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
cimport cython
from cpython.mem cimport PyMem_Malloc, PyMem_Free
ctypedef unsigned long long ull
ctypedef unsigned int idx_t

cdef extern from *:
    unsigned int __builtin_popcountll(unsigned long long) nogil
    unsigned int __builtin_ctzll(unsigned long long) nogil

cdef inline int bc(ull x) nogil:
    return <int>__builtin_popcountll(x)

cdef inline idx_t ctz(ull x) nogil:
    return <idx_t>__builtin_ctzll(x)
cdef inline int color_bound(ull P, ull* neighbors) nogil:
    cdef ull uncol = P, cur, v
    cdef int color = 0
    cdef idx_t i
    while uncol:
        color += 1
        cur = uncol
        while cur:
            v = cur & -cur
            cur -= v
            uncol &= ~v
            i = ctz(v)
            cur &= ~neighbors[i]
    return color
cdef void bronk(ull R, ull P, ull X, int *best_size_p, ull *bestR_p, ull* neighbors, idx_t n) nogil:
    cdef int sizeR = bc(R)
    if P == 0 and X == 0:
        if sizeR > best_size_p[0]:
            best_size_p[0] = sizeR
            bestR_p[0] = R
        return
    if sizeR + bc(P) <= best_size_p[0]:
        return
    cdef int bound = color_bound(P, neighbors)
    if sizeR + bound <= best_size_p[0]:
        return
    cdef ull PX = P | X
    cdef int maxd = -1
    cdef idx_t u = 0
    cdef ull tmp = PX, v
    cdef idx_t i
    cdef int d
    while tmp:
        v = tmp & -tmp
        tmp -= v
        i = ctz(v)
        d = bc(P & neighbors[i])
        if d > maxd:
            maxd = d
            u = i
    cdef ull ext = P & ~neighbors[u]
    tmp = ext
    while tmp:
        v = tmp & -tmp
        tmp -= v
        i = ctz(v)
        bronk(R | v, P & neighbors[i], X & neighbors[i], best_size_p, bestR_p, neighbors, n)
        P &= ~v
        X |= v

def solve_c(object problem):
    cdef Py_ssize_t n = len(problem)
    cdef ull* neighbors = <ull*> PyMem_Malloc(n * sizeof(ull))
    cdef Py_ssize_t i, j
    cdef ull mask, full
    cdef int best_size
    cdef ull bestR
    cdef int* best_size_p = &best_size
    cdef ull* bestR_p = &bestR

    full = (<ull>1 << n) - 1
    for i in range(n):
        mask = full & ~(<ull>1 << i)
        for j in range(n):
            if (<int>problem[i][j]):
                mask &= ~(<ull>1 << j)
        neighbors[i] = mask

    # greedy lower bound
    cdef list order = list(range(n))
    order.sort(key=lambda x: (neighbors[x]).bit_count())
    cdef ull R0 = 0
    for i in order:
        if (R0 & neighbors[i]) == R0:
            R0 |= (<ull>1 << i)

    best_size = bc(R0)
    bestR = R0

    bronk(<ull>0, full, <ull>0, best_size_p, bestR_p, neighbors, <idx_t>n)

    # extract result
    cdef list res = []
    for i in range(n):
        if (bestR >> i) & 1:
            res.append(i)

    PyMem_Free(neighbors)
    return res
EOF

/usr/local/bin/pip install .

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
