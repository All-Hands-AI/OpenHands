#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy.fftpack import dstn

class Solver:
    def solve(self, problem, **kwargs):
        """
        Compute the 2‑D Discrete Sine Transform (DST) Type II of a real‑valued square matrix.
        Uses scipy.fftpack.dstn with in‑place computation for optimal performance.
        """
        # Ensure input is a NumPy array (single‑precision for speed)
        a = np.asarray(problem, dtype=np.float32)
        # Compute 2‑D DST‑II in a single call, overwriting the input
        result = dstn(a, type=2, norm=None, overwrite_x=True)
        return result
EOF
