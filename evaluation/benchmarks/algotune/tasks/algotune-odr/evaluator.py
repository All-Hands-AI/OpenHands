# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
from typing import Any

import numpy as np
import scipy.odr as odr



class Task:
    """Benchmark fitting a weighted ODR with ``scipy.odr``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Any other specific initialization for ODR can go here
        pass

    def generate_problem(self, n: int, random_seed: int = 1729) -> dict[str, Any]:
        """Generate a simulated ODR problem from analytical chemistry.

        Params
        ------
        n : int
            The total number of true concentrations at which measurements are being
            made.
        random_seed : int
            A random seed for the random number generator used.

        Returns
        -------
        dict
            A dictionary with keys:
            "x": Mean measurements of concentration of chemical C taken by an analytical
                 method X over 100 replicates taken from n samples of increasing but
                 unknown true concentration.
            "y": Mean measurements of concentration of chemical C taken by an analytical
                 method Y over 100 replicates taken from n samples of increasing but
                 unknown true concentration.
            "sx": The associated standard errors to the mean measurements in "x". This
                  is the sample standard deviation over the replicates for a method at
                  a given concentration divided by the square root of the number of
                  replicates.
            "sy": The associated standard errors to the mean measurements in "y".
        """
        num_replicates = 100
        rng = np.random.default_rng(random_seed)

        # The unknown true concentrations increase quadratically.
        target_concentrations = np.arange(1, n + 1) ** 2

        # The unknown true standard deviations of measurements made by each
        # method as a function of concentration is linear with a randomly chosen
        # slope and intercept.
        method_X_noise = rng.uniform(0, 1) + rng.uniform(1, 3) * target_concentrations
        method_Y_noise = rng.uniform(0, 1) + rng.uniform(1, 3) * target_concentrations

        # Assume the "true relationship" between mean measurements made by method X as
        # a function of concentration and mean measurements made by method Y as a
        # a function of concentration takes the form f(x) = (a + b*x) / (1 + h*x).
        a = np.random.uniform(0, 5)
        b = np.random.uniform(0.75, 1.25)
        h = np.random.uniform(0, 0.001)

        def f(x):
            return (a + b * x) / (1 + h * x)

        # Sample 100 replicates for each method at each concentration.
        x_replicates = (
            target_concentrations[:, np.newaxis]
            + rng.normal(loc=0.0, scale=method_X_noise, size=(num_replicates, n)).T
        )
        y_replicates = (
            f(target_concentrations[:, np.newaxis])
            + rng.normal(loc=0.0, scale=method_Y_noise, size=(num_replicates, n)).T
        )

        # Calculate means and standard errors.
        x, y = x_replicates.mean(axis=1), y_replicates.mean(axis=1)
        sx, sy = x_replicates.std(axis=1, ddof=1), y_replicates.std(axis=1, ddof=1)
        sx, sy = sx / np.sqrt(num_replicates), sy / np.sqrt(num_replicates)

        return {"x": x.tolist(), "y": y.tolist(), "sx": sx.tolist(), "sy": sy.tolist()}

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Fit weighted ODR with scipy.odr."""
        x = np.asarray(problem["x"])
        y = np.asarray(problem["y"])
        sx = np.asarray(problem["sx"])
        sy = np.asarray(problem["sy"])

        data = odr.RealData(x, y=y, sx=sx, sy=sy)
        model = odr.Model(lambda B, x: B[0] * x + B[1])
        output = odr.ODR(data, model, beta0=[0.0, 1.0]).run()
        return {"beta": output.beta.tolist()}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """Verify fit slope and intercept are close to the reference."""
        beta_expected = self.solve(problem)["beta"]
        beta_observed = solution["beta"]
        # The default rtol for coefficents in `scipy.odr` is machine epsilon
        # to the 2/3 power. Double it here to account for the possibility that an
        # LLM comes up with something equally accurate, but in the opposite
        # direction.
        rtol = 2 * np.finfo(float).eps ** (2 / 3)
        # An atol shouldn't be necessary, but put something very small here to
        # account for the rare chance that subnormal or zero coefficient is fit
        # by the reference.
        atol = np.finfo(float).smallest_normal
        return np.allclose(beta_observed, beta_expected, atol=atol, rtol=rtol)