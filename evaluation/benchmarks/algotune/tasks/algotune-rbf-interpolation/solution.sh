#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy.interpolate import RBFInterpolator

class Solver:
    def solve(self, problem, **kwargs) -> dict:
        """
        Reference-wrapping solver using SciPy's RBFInterpolator for correctness.
        """
        x_train = np.asarray(problem["x_train"], dtype=float)
        y_train = np.asarray(problem["y_train"], dtype=float).ravel()
        x_test = np.asarray(problem["x_test"], dtype=float)

        rbf_config = problem.get("rbf_config", {})
        kernel = rbf_config.get("kernel")
        epsilon = rbf_config.get("epsilon")
        smoothing = rbf_config.get("smoothing")

        rbf = RBFInterpolator(
            x_train, y_train, kernel=kernel, epsilon=epsilon, smoothing=smoothing
        )
        y_pred = rbf(x_test)

        return {
            "y_pred": y_pred.tolist(),
            "rbf_config": {"kernel": kernel, "epsilon": epsilon, "smoothing": smoothing},
        }
EOF
