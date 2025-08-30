# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import numpy as np
from scipy.integrate import tanhsinh
from scipy.special import wright_bessel



class Task:
    """Benchmark scipy.integrate.tansinh for elementwise 1d integration."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Any other specific initialization for ElementWiseIntegration can go here
        pass

    def generate_problem(self, n: int, random_seed: int = 1729) -> dict[str, Any]:
        """Elemenwise integration of Wright's Bessel function.

        Returns a dictionary with keys
        "a": list containing `n` values of `wright_bessel` parameter `a`.
        "b": list containing `n` values for `wright_bessel` parameter `b`.
        "lower": list containing `n` values for the lower limit of integration.
        "upper": list conta `n` values for the upper limit of integration.

        I chose Wright's Bessel function because I suspect it would be very
        difficult to "cheat" by using methods other than numerical integration.
        Of course, an LLM does work out an efficient implementation of the
        integral of the Wright Bessel function by e.g. integrating the defining
        series term by term, that would be very interesting in its own right.
        """
        rng = np.random.default_rng(random_seed)
        a = rng.uniform(0.5, 4, size=n)
        b = rng.uniform(0.5, 4, size=n)
        # Ensure there's a gap between lower and upper to avoid numerically
        # difficult cases where lower and upper are very close.
        lower = rng.uniform(0, 10 / 3, size=n)
        upper = rng.uniform(20 / 3, 10, size=n)
        lower, upper = np.minimum(lower, upper), np.maximum(lower, upper)
        return {"a": a.tolist(), "b": b.tolist(), "lower": lower.tolist(), "upper": upper.tolist()}

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Solve integration problem with scipy.integrate.tanhsinh."""
        a = problem["a"]
        b = problem["b"]
        lower = problem["lower"]
        upper = problem["upper"]
        res = tanhsinh(wright_bessel, lower, upper, args=(a, b))
        # This assert is a sanity check. The goal was to create problems where
        # the integrator always converges using the default tolerances. If this
        # ever fails, then `generate_problem` should be fixed.
        assert np.all(res.success)
        return {"result": res.integral.tolist()}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """Verify solution."""
        reference = self.solve(problem)
        rtol = np.finfo(float).eps ** 0.5
        return np.allclose(solution["result"], reference["result"], rtol=rtol)