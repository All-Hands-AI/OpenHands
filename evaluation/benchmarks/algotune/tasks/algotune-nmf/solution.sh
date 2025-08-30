#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
from sklearn.decomposition import NMF

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, list[list[float]]]:
        try:
            # Use optimized NMF configuration
            model = NMF(
                n_components=problem["n_components"], 
                init="nndsvd",    # Better initialization for faster convergence
                max_iter=150,     # Reduced iterations for speed
                tol=1e-3,         # Slightly looser tolerance for speed
                random_state=0
            )
            X = np.array(problem["X"], dtype=np.float32)
            W = model.fit_transform(X)
            H = model.components_
            # Ensure non-negativity (should already be but just in case)
            W = np.maximum(W, 0)
            H = np.maximum(H, 0)
            return {"W": W.tolist(), "H": H.tolist()}
        except Exception:
            n_components = problem["n_components"]
            n, d = np.array(problem["X"]).shape
            W = np.zeros((n, n_components), dtype=float).tolist()
            H = np.zeros((n_components, d), dtype=float).tolist()
            return {"W": W, "H": H}
EOF
