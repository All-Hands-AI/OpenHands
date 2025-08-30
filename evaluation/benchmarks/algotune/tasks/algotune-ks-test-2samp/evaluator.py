# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import numpy as np
import scipy.stats as stats



class Task:
    """Benchmark two sample kolmogorov smirnov test against `scipy.stats.ks_2samp`."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    def generate_problem(self, n: int, random_seed: int = 1729) -> dict[str, Any]:
        """Generate two iid samples from a Cauchy distribution.
        This task was chosen deliberately so that pvalues would neither underflow
        (zero or subnormal) or be likely to always be 1, even when the sample size
        grows very large.
        Parameters
        ----------
        n : int
            The number of points to draw in each sample.
        random_seed : int
            A random seed for reproducibility.
        Returns
        -------
        dict
            A dictionary with keys ``"sample1"`` and ``"sample2"`` containing lists
            of `n` double precision floating point numbers each, representing two
            independent samples of size n from a Cauchy distribution.
        """
        rng = np.random.default_rng(random_seed)
        dist = stats.cauchy()
        sample1 = dist.rvs(size=n, random_state=rng)
        sample2 = dist.rvs(size=n, random_state=rng)
        return {"sample1": sample1.tolist(), "sample2": sample2.tolist()}

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Peform two sample ks test to get statistic and pvalue."""
        result = stats.ks_2samp(problem["sample1"], problem["sample2"], method="auto")
        return {"statistic": result.statistic, "pvalue": result.pvalue}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """Verify solution agains the reference."""
        tmp = self.solve(problem)
        expected_result = np.asarray([tmp["statistic"], tmp["pvalue"]])
        observed_result = np.asarray([solution["statistic"], solution["pvalue"]])
        rtol = np.finfo(float).eps ** 0.5
        atol = np.finfo(float).smallest_normal
        return np.allclose(observed_result, expected_result, rtol=rtol, atol=atol)