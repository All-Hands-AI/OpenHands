#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from typing import Any

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Perform two sample KS test to get statistic and pvalue."""
        sample1 = np.asarray(problem["sample1"], dtype=np.float64)
        sample2 = np.asarray(problem["sample2"], dtype=np.float64)
        
        n1 = len(sample1)
        n2 = len(sample2)
        
        # Use scipy but with optimized method selection
        import scipy.stats as stats
        
        # For small samples, use exact method; for large, use asymptotic
        if n1 * n2 < 10000:
            result = stats.ks_2samp(sample1, sample2, method="exact")
        else:
            result = stats.ks_2samp(sample1, sample2, method="asymp")
        
        return {"statistic": result.statistic, "pvalue": result.pvalue}
EOF
