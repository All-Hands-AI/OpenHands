# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random

import numpy as np



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the PolynomialReal Task.

        :param kwargs: Keyword arguments.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> list[float]:
        """
        Generate a polynomial problem with a polynomial of degree n having all real roots.

        The polynomial is constructed by:
          1) Asserting that n >= 1.
          2) Sampling n distinct real roots as floating point numbers (rounded to 6 decimal points)
             from the interval [-1, 1].
          3) Computing the polynomial coefficients from the roots using NumPy's poly function.

        The resulting polynomial p(x) is given by:
            p(x) = aₙxⁿ + aₙ₋₁xⁿ⁻¹ + ... + a₀,
        and the coefficients are returned as a list in descending order.

        Increasing n makes the problem harder due to a larger number of roots and higher numerical instability.

        :param n: Degree of the polynomial (must be ≥ 1).
        :param random_seed: Seed for reproducibility.
        :raises ValueError: If n < 1.
        :return: A list of polynomial coefficients (real numbers) in descending order.
        """
        logging.debug(f"Starting generate_problem with n={n}, random_seed={random_seed}")
        random.seed(random_seed)

        if n < 1:
            raise ValueError("Polynomial degree must be at least 1.")

        lower_bound = -1
        upper_bound = 1

        # Generate n distinct real roots.
        true_roots_set = set()
        while len(true_roots_set) < n:
            candidate = round(random.uniform(lower_bound, upper_bound), 6)
            true_roots_set.add(candidate)
        true_roots = sorted(list(true_roots_set))

        # Compute polynomial coefficients from the roots.
        # np.poly returns coefficients for p(x) = aₙxⁿ + ... + a₀.
        coefficients = np.poly(true_roots).tolist()

        logging.debug(f"Generated polynomial of degree {n} with coefficients={coefficients}")
        return coefficients

    def solve(self, problem: list[float]) -> list[float]:
        """
        Solve the polynomial problem by finding all real roots of the polynomial.

        The polynomial is given as a list of coefficients [aₙ, aₙ₋₁, ..., a₀],
        representing:
            p(x) = aₙxⁿ + aₙ₋₁xⁿ⁻¹ + ... + a₀.
        This method computes the roots, converts them to real numbers if their imaginary parts are negligible,
        and returns them sorted in decreasing order.

        :param problem: A list of polynomial coefficients (real numbers) in descending order.
        :return: A list of real roots of the polynomial, sorted in decreasing order.
        """
        coefficients = problem
        computed_roots = np.roots(coefficients)
        # Convert roots to real numbers if the imaginary parts are negligible (tol=1e-3)
        computed_roots = np.real_if_close(computed_roots, tol=1e-3)
        computed_roots = np.real(computed_roots)
        # Sort roots in decreasing order.
        computed_roots = np.sort(computed_roots)[::-1]
        logging.debug(f"Computed roots (decreasing order): {computed_roots.tolist()}")
        return computed_roots.tolist()

    def is_solution(self, problem: list[float], solution: list[float]) -> bool:
        """
        Check if the polynomial root solution is valid and optimal.

        A valid solution must:
        1. Match the reference solution (computed using np.roots) within a small tolerance
        2. Be sorted in descending order

        :param problem: A list of polynomial coefficients (real numbers) in descending order.
        :param solution: A list of computed real roots.
        :return: True if the solution is valid and optimal, False otherwise.
        """
        coefficients = problem
        reference_roots = np.roots(coefficients)
        reference_roots = np.real_if_close(reference_roots, tol=1e-3)
        reference_roots = np.real(reference_roots)
        reference_roots = np.sort(reference_roots)[::-1]
        candidate = np.array(solution)
        reference = np.array(reference_roots)
        tol = 1e-6
        error = np.linalg.norm(candidate - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(f"Polynomial real solution error {error} exceeds tolerance {tol}.")
            return False
        return True