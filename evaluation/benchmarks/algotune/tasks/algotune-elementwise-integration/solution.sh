#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
import importlib

# Dynamic import of SciPy special and integrator
_special = importlib.import_module("scipy.special")
_wright_bessel = getattr(_special, "wright_bessel")
_intmod = importlib.import_module("scipy.integrate")
_tanhsinh = getattr(_intmod, "tanhsinh")

class Solver:
    def solve(self, problem, **kwargs):
        """
        Integrate Wright’s Bessel Φ(a,b;x) on [lower[i],upper[i]]
        using SciPy’s tanhsinh for full accuracy.
        """
        a = problem["a"]
        b = problem["b"]
        lower = problem["lower"]
        upper = problem["upper"]
        res = _tanhsinh(_wright_bessel, lower, upper, args=(a, b))
        assert np.all(res.success)
        return {"result": res.integral.tolist()}
EOF
