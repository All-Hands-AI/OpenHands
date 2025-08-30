# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import hmac
import logging
import random
from typing import Any

from cryptography.hazmat.primitives import hashes



HASH_SIZE = 32  # SHA-256 produces a 32-byte (256-bit) digest


class Task:
    """
    Sha256Hashing Task:

    In this task, you are given a plaintext message.
    The task is to compute its SHA-256 hash digest using the cryptography library.
    """

    DEFAULT_PLAINTEXT_MULTIPLIER = 1024  # Bytes of plaintext per unit of n

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random plaintext of size scaled by n.

        Although n is provided for scaling, the generated problem contains only the plaintext.
        The size of the plaintext is n * DEFAULT_PLAINTEXT_MULTIPLIER bytes.

        :param n: The scaling parameter that determines plaintext size.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the SHA-256 hashing problem with key:
                 "plaintext": A bytes object to be hashed.
        """
        # Use n to scale the plaintext size
        plaintext_size = max(1, n * self.DEFAULT_PLAINTEXT_MULTIPLIER)  # Ensure at least 1 byte

        logging.debug(
            f"Generating SHA-256 problem with n={n} "
            f"(plaintext_size={plaintext_size}), random_seed={random_seed}"
        )

        random.seed(random_seed)
        plaintext = random.randbytes(plaintext_size)

        return {
            "plaintext": plaintext,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, bytes]:
        """
        Compute the SHA-256 hash of the plaintext using the cryptography library.
        Uses cryptography.hazmat.primitives.hashes to compute the digest.

        :param problem: A dictionary containing the problem with key "plaintext".
        :return: A dictionary with key "digest" containing the SHA-256 hash value.
        """
        plaintext = problem["plaintext"]

        try:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(plaintext)
            hash_value = digest.finalize()

            return {"digest": hash_value}

        except Exception as e:
            logging.error(f"Error during SHA-256 hashing in solve: {e}")
            raise

    def is_solution(self, problem: dict[str, Any], solution: dict[str, bytes] | Any) -> bool:
        """
        Check if the SHA-256 hash solution is valid and optimal.

        This method checks:
          - The solution contains the 'digest' key
          - The digest is a bytes object
          - The digest matches the result from self.solve()

        :param problem: A dictionary containing the problem with key "plaintext".
        :param solution: A dictionary containing the hash solution with key "digest".
        :return: True if the solution matches the result from self.solve().
        """
        if not isinstance(solution, dict) or "digest" not in solution:
            logging.error(
                f"Invalid solution format. Expected dict with 'digest'. Got: {type(solution)}"
            )
            return False

        try:
            # Get the correct result by calling the solve method
            reference_result = self.solve(problem)
            reference_digest = reference_result["digest"]
        except Exception as e:
            # If solve itself fails, we cannot verify the solution
            logging.error(f"Failed to generate reference solution in is_solution: {e}")
            return False

        solution_digest = solution["digest"]

        # Ensure digest is bytes before comparison
        if not isinstance(solution_digest, bytes):
            logging.error("Solution 'digest' is not bytes.")
            return False

        return hmac.compare_digest(reference_digest, solution_digest)