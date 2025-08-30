#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import os
import multiprocessing

# Enable BLAS/LAPACK multithreading using available CPU cores
_threads = multiprocessing.cpu_count()
os.environ["OPENBLAS_NUM_THREADS"] = str(_threads)
os.environ["OMP_NUM_THREADS"] = str(_threads)
os.environ["MKL_NUM_THREADS"] = str(_threads)

import numpy as np
from scipy.linalg import qz

class Solver:
    def solve(self, problem, **kwargs):
        # Prepare Fortran-contiguous input arrays in double precision
        A = np.asarray(problem["A"], dtype=np.double, order='F')
        B = np.asarray(problem["B"], dtype=np.double, order='F')
        # Compute real QZ decomposition with minimal overhead
        AA, BB, Q, Z = qz(
            A, B,
            output='real',
            overwrite_a=True, overwrite_b=True,
            check_finite=False
        )
        # Return factors directly; harness will convert and validate
        return {
            "QZ": {
                "AA": AA,
                "BB": BB,
                "Q": Q,
                "Z": Z,
            }
        }
EOF
