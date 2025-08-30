#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy import signal
from typing import Any

class Solver:
    def solve(self, problem: list, **kwargs) -> Any:
        """
        Compute the 1D correlation for each valid pair in the problem list.
        """
        mode = kwargs.get("mode", "full")
        results = []
        
        # Filter pairs for 'valid' mode first to avoid unnecessary processing
        if mode == "valid":
            pairs_to_process = [(a, b) for a, b in problem if b.shape[0] <= a.shape[0]]
        else:
            pairs_to_process = problem
            
        for a, b in pairs_to_process:
            res = signal.correlate(a, b, mode=mode, method='auto')
            results.append(res)
            
        return results
EOF
