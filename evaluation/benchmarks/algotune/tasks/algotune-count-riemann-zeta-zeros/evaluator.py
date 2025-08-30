# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import numpy as np
from mpmath import mp



class Task:
    """Count the number of Riemann Zeta zeros in critical strip.

    Count zeros in the critical strip with imaginary part <= t,
    e.g. ``(0, 1) x (0, t]``.

    Benchmark comparison against `mpmath.mp.zetazero`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Any other specific initialization for CountRiemannZetaZeros can go here
        pass

    def generate_problem(self, n: int, random_seed: int = 1729) -> dict[str, Any]:
        """Generate t that scales linearly with n."""
        rng = np.random.default_rng(random_seed)
        c = rng.uniform(0.6666666666666666, 1.5)
        t = c * n
        return {"t": t}

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Count zeta zeros along critical strip with imaginary part <= t.

        Using `mpmath.mp.nzeros`.
        """
        result = mp.nzeros(problem["t"])
        return {"result": result}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """Verify solution by comparing to reference."""
        expected_solution = self.solve(problem)["result"]
        observed_solution = solution["result"]
        return expected_solution == observed_solution