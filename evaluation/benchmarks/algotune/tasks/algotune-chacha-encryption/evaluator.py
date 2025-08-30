# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import hmac
import logging
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305



CHACHA_KEY_SIZE = 32  # ChaCha20 uses 256-bit keys
CHACHA_NONCE_SIZE = 12  # 96-bit nonce for ChaCha20-Poly1305
POLY1305_TAG_SIZE = 16  # 128-bit authentication tag
ASSOCIATED_DATA_SIZE = 32  # Size of associated data (optional, can be empty)


class Task:
    DEFAULT_PLAINTEXT_MULTIPLIER = 1024  # Bytes of plaintext per unit of n

    def __init__(self, **kwargs):
        """
        Initialize the ChaChaEncryption task.

        In this task, you are given a plaintext, key, nonce, and optional associated data.
        The task is to compute the ChaCha20-Poly1305 encryption such that:
            ciphertext, tag = ChaCha20Poly1305(key).encrypt(nonce, plaintext, associated_data)
        where ciphertext is the encrypted data and tag is the authentication tag.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate random encryption inputs scaled by n.

        The dimensions of the plaintext scale with n, while key and nonce remain fixed size.

        :param n: The scaling factor that determines plaintext size.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the encryption problem with keys:
                 "key": The ChaCha20 key (32 bytes)
                 "nonce": The nonce (12 bytes * NUM_CHUNKS) to use for encryption
                 "plaintext": The data to encrypt (size scales with n)
                 "associated_data": Optional authenticated data
        """
        plaintext_size = max(1, n * self.DEFAULT_PLAINTEXT_MULTIPLIER)
        if plaintext_size > 2**31 - 1:
            raise ValueError(
                f"Plaintext size ({plaintext_size}) exceeds maximum allowed size ({2**31 - 1})."
            )

        logging.debug(
            f"Generating ChaCha20-Poly1305 problem with n={n} "
            f"(plaintext_size={plaintext_size}), random_seed={random_seed}"
        )

        # Use os.urandom and .generate_key() for cryptographic randomness.
        # While random_seed is an input, for crypto tasks, using truly random
        # keys/nonces per problem instance is generally better practice,
        # even if it makes the benchmark non-deterministic w.r.t random_seed.
        key = ChaCha20Poly1305.generate_key()
        nonce = os.urandom(CHACHA_NONCE_SIZE)
        plaintext = os.urandom(plaintext_size)
        associated_data = os.urandom(ASSOCIATED_DATA_SIZE) if n % 2 == 0 else b""

        return {
            "key": key,
            "nonce": nonce,
            "plaintext": plaintext,
            "associated_data": associated_data,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, bytes]:
        """
        Solve the ChaCha20-Poly1305 encryption problem by encrypting the plaintext.
        Uses cryptography.hazmat.primitives.ciphers.aead.ChaCha20Poly1305 to compute:
            ciphertext, tag = encrypt(key, nonce, plaintext, associated_data)

        :param problem: A dictionary containing the encryption inputs.
        :return: A dictionary with keys:
                 "ciphertext": The encrypted data
                 "tag": The authentication tag (16 bytes)
        """
        key = problem["key"]
        nonce = problem["nonce"]
        plaintext = problem["plaintext"]
        associated_data = problem["associated_data"]

        try:
            if len(key) != CHACHA_KEY_SIZE:
                raise ValueError(f"Invalid key size: {len(key)}. Must be {CHACHA_KEY_SIZE}.")

            chacha = ChaCha20Poly1305(key)
            ciphertext = chacha.encrypt(nonce, plaintext, associated_data)

            if len(ciphertext) < POLY1305_TAG_SIZE:
                raise ValueError("Encrypted output is shorter than the expected tag size.")

            actual_ciphertext = ciphertext[:-POLY1305_TAG_SIZE]
            tag = ciphertext[-POLY1305_TAG_SIZE:]

            return {"ciphertext": actual_ciphertext, "tag": tag}

        except Exception as e:
            logging.error(f"Error during ChaCha20-Poly1305 encryption in solve: {e}")
            raise

    def is_solution(self, problem: dict[str, Any], solution: dict[str, bytes] | Any) -> bool:
        """
        Check if the encryption solution is valid and optimal.

        This method checks:
          - The solution contains 'ciphertext' and 'tag' keys
          - Both values are bytes objects
          - The ciphertext and tag match the reference solution from solve()
          - The tag is the correct length (16 bytes)

        :param problem: A dictionary containing the encryption inputs
        :param solution: A dictionary containing the encryption solution with keys
                        "ciphertext" and "tag"
        :return: True if the solution is valid and optimal, False otherwise
        """
        if not isinstance(solution, dict) or "ciphertext" not in solution or "tag" not in solution:
            logging.error(
                f"Invalid solution format. Expected dict with 'ciphertext' and 'tag'. Got: {type(solution)}"
            )
            return False

        try:
            reference_result = self.solve(problem)
            reference_ciphertext = reference_result["ciphertext"]
            reference_tag = reference_result["tag"]
        except Exception as e:
            logging.error(f"Failed to generate reference solution in is_solution: {e}")
            return False

        solution_ciphertext = solution["ciphertext"]
        solution_tag = solution["tag"]

        if not isinstance(solution_ciphertext, bytes) or not isinstance(solution_tag, bytes):
            logging.error("Solution 'ciphertext' or 'tag' is not bytes.")
            return False

        ciphertext_match = hmac.compare_digest(reference_ciphertext, solution_ciphertext)
        tag_match = hmac.compare_digest(reference_tag, solution_tag)

        return ciphertext_match and tag_match