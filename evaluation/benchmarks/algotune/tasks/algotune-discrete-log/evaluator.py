# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random

import sympy
from sympy.ntheory.residue_ntheory import discrete_log



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the DiscreteLog task.

        In this task, you are given a prime number p, a generator g, and a value h.
        The task is to compute the discrete logarithm x such that:
            g^x ≡ h (mod p)
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, int]:
        """
        Generate a discrete logarithm problem.

        The parameter n controls the size of the problem: larger n values result in
        larger primes p, making the problem more challenging.

        :param n: Parameter controlling the size of the problem.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the discrete logarithm problem with keys:
                 "p": A prime number.
                 "g": A generator element in the multiplicative group of integers modulo p.
                 "h": A value h for which we want to find x such that g^x ≡ h (mod p).
        """
        logging.debug(
            f"Generating discrete logarithm problem with n={n} and random_seed={random_seed}"
        )
        # Create explicit RNG instance instead of modifying global state
        rng = random.Random(random_seed)

        # Generate a prime p with bit length determined by n
        bits = 16 + n  # Even slower growth rate for prime size

        # Generate a random prime with the calculated number of bits
        p = sympy.nextprime(rng.randint(2 ** (bits - 1), 2**bits - 1))

        # Choose a generator g (for simplicity, we'll use a random element)
        # In practice, finding a generator can be complex, so we use a random element
        # that has a high probability of generating a large subgroup
        g = rng.randint(2, p - 1)

        # Choose a random exponent x and compute h = g^x mod p
        x = rng.randint(2, p - 1)
        h = pow(g, x, p)

        logging.debug(f"Generated discrete logarithm problem with p={p}, g={g}, x={x}, h={h}.")
        return {"p": int(p), "g": int(g), "h": int(h)}

    def solve(self, problem: dict[str, int]) -> dict[str, int]:
        """
        Solve the discrete logarithm problem using sympy's discrete_log function.

        This function implements algorithms for computing discrete logarithms
        including baby-step giant-step and Pohlig-Hellman.

        :param problem: A dictionary representing the discrete logarithm problem.
        :return: A dictionary with key "x" containing the discrete logarithm solution.
        """
        p = problem["p"]
        g = problem["g"]
        h = problem["h"]

        # discrete_log(p, h, g) computes x such that g^x ≡ h (mod p)
        return {"x": discrete_log(p, h, g)}

    def is_solution(self, problem: dict[str, int], solution: dict[str, int]) -> bool:
        """
        Check if the discrete logarithm solution is valid.

        This method checks if g^x ≡ h (mod p) for the provided solution x.

        :param problem: A dictionary containing the problem with keys "p", "g", and "h".
        :param solution: A dictionary containing the discrete logarithm solution with key "x".
        :return: True if the solution is valid, False otherwise.
        """
        # Check if problem and solution are dictionaries
        if not isinstance(problem, dict):
            logging.error("Problem is not a dictionary.")
            return False

        if not isinstance(solution, dict):
            logging.error("Solution is not a dictionary.")
            return False

        p = problem.get("p")
        g = problem.get("g")
        h = problem.get("h")

        if p is None or g is None or h is None:
            logging.error("Problem is missing required keys (p, g, h).")
            return False

        if "x" not in solution:
            logging.error("Solution does not contain 'x' key.")
            return False

        x = solution["x"]

        # Verify that g^x ≡ h (mod p)
        if pow(g, x, p) != h:
            logging.error(f"Solution verification failed: g^x ≢ h (mod p). {pow(g, x, p)} != {h}")
            return False

        # All checks passed
        return True