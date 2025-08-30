#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from numpy.linalg import qr as _nqr
# Attempt to use SciPy's QR for potential speed benefits
_use_scipy = False
try:
    from scipy.linalg import qr as _sqr
    # test SciPy QR API compatibility; use disorder check to skip extra copying
    _sqr(np.zeros((1,2), dtype=float, order='F'), mode='economic', overwrite_a=True, check_finite=False)
    _use_scipy = True
except Exception:
    _sqr = None

class Solver:
    def solve(self, problem, **kwargs):
        # Convert input to Fortran-contiguous float64 array
        A = np.array(problem["matrix"], dtype=np.float64, order='F')
        if _use_scipy:
            # Use SciPy's QR with overwrite to avoid extra copies, skip finiteness check
            Q, R = _sqr(A, mode='economic', overwrite_a=True, check_finite=False)
        else:
            Q, R = _nqr(A, mode="reduced")
        return {"QR": {"Q": Q, "R": R}}
EOF
