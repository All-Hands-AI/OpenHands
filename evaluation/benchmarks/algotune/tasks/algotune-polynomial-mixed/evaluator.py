# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random

import numpy as np



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the PolynomialMixed Task.

        :param kwargs: Keyword arguments.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> list[float]:
        """
        Generate a polynomial problem of degree n with real coefficients.

        The polynomial is constructed so that it has a mix of real and complex roots.
        Since the polynomial has real coefficients, any non-real roots appear in conjugate pairs.
        This method returns a list of polynomial coefficients (real numbers) in descending order,
        representing the polynomial:
            p(x) = a_n * x^n + a_{n-1} * x^{n-1} + ... + a_0.

        :param n: Degree of the polynomial (must be ≥ 1).
        :param random_seed: Seed for reproducibility.
        :raises ValueError: If n < 1.
        :return: A list of polynomial coefficients (real numbers) in descending order.
        """
        logging.debug(f"Starting generate_problem with n={n}, random_seed={random_seed}")
        random.seed(random_seed)

        if n < 1:
            raise ValueError("Polynomial degree must be at least 1.")

        # Determine the number of real roots (r) such that (n - r) is even.
        possible_r = [r for r in range(1, n + 1) if (n - r) % 2 == 0]
        r = random.choice(possible_r)
        c = (n - r) // 2  # number of complex conjugate pairs

        # Generate r distinct real roots.
        real_roots = set()
        while len(real_roots) < r:
            candidate = round(random.uniform(-1, 1), 6)
            real_roots.add(candidate)
        real_roots = list(real_roots)

        # Generate c distinct complex roots (with nonzero imaginary parts).
        complex_roots = set()
        while len(complex_roots) < c:
            real_part = round(random.uniform(-1, 1), 6)
            imag_part = round(random.uniform(-1, 1), 6)
            if abs(imag_part) < 1e-6:
                continue
            candidate = complex(real_part, imag_part)
            complex_roots.add(candidate)
        complex_roots = list(complex_roots)

        # Include each complex root and its conjugate.
        roots = real_roots + [
            z for pair in complex_roots for z in (pair, complex(pair.real, -pair.imag))
        ]

        # Shuffle the roots to remove any ordering.
        random.shuffle(roots)

        # Compute polynomial coefficients from the roots.
        # Since the roots occur in conjugate pairs, the resulting coefficients are real.
        coefficients = np.poly(roots).tolist()
        logging.debug(f"Generated polynomial of degree {n} with coefficients={coefficients}")
        return coefficients

    def solve(self, problem: list[float]) -> list[complex]:
        """
        Solve the polynomial problem by finding all roots of the polynomial.

        The polynomial is given as a list of coefficients [a_n, a_{n-1}, ..., a_0],
        representing p(x) = a_n * x^n + a_{n-1} * x^{n-1} + ... + a_0.
        The coefficients are real numbers.
        This method computes all the roots (which may be real or complex) and returns them
        sorted in descending order by their real parts and, if necessary, by their imaginary parts.

        :param problem: A list of polynomial coefficients (real numbers) in descending order.
        :return: A list of roots (real and complex) sorted in descending order.
        """
        coefficients = problem
        computed_roots = np.roots(coefficients)
        sorted_roots = sorted(computed_roots, key=lambda z: (z.real, z.imag), reverse=True)
        logging.debug(f"Computed roots (descending order): {sorted_roots}")
        return sorted_roots

    def is_solution(self, problem: list[float], solution: list[complex]) -> bool:
        """
        Check if the polynomial root solution is valid and optimal.

        A valid solution must:
        1. Match the reference solution (computed using np.roots) within a small tolerance
        2. Be sorted in the correct order (by real part, then imaginary part, descending)

        :param problem: A list of polynomial coefficients (real numbers) in descending order.
        :param solution: A list of computed roots (real and complex numbers).
        :return: True if the solution is valid and optimal, False otherwise.
        """
        coefficients = problem
        reference_roots = np.roots(coefficients)
        sorted_reference = sorted(reference_roots, key=lambda z: (z.real, z.imag), reverse=True)
        candidate = np.array(solution)
        reference = np.array(sorted_reference)
        tol = 1e-6
        error = np.linalg.norm(candidate - reference) / (np.linalg.norm(reference) + 1e-12)
        if error > tol:
            logging.error(f"Polynomial mixed solution error {error} exceeds tolerance {tol}.")
            return False
        return True