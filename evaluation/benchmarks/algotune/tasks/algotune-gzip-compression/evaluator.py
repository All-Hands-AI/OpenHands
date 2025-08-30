# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import gzip
import logging
import math  # Added for ceiling function
import string  # Needed for random word generation
from typing import Any

import numpy as np



class Task:
    """
    GzipCompression Task:

    Compress binary data (generated using a Zipfian distribution of words)
    using the gzip algorithm with mtime set to 0 for deterministic output.
    The difficulty scales with the size of the input data.
    """

    # Constants for data generation (similar to base64_encoding)
    DEFAULT_PLAINTEXT_MULTIPLIER = 2048  # Target bytes of plaintext per unit of n
    VOCABULARY_SIZE = 1000  # Number of unique words in our vocabulary
    ZIPF_PARAMETER_A = 1.2  # Parameter 'a' for the Zipf distribution (> 1)
    # Constants for data generation
    DEFAULT_PLAINTEXT_MULTIPLIER = 2048  # Target bytes of plaintext per unit of n
    # Image-like data constants (Using Perlin Noise)
    PERLIN_RES = (4, 4)
    PERLIN_OCTAVES = 4
    PERLIN_PERSISTENCE = 0.5
    PERLIN_LACUNARITY = 2
    # Text-like data constants
    VOCABULARY_SIZE = 10000
    ZIPF_PARAMETER_A = 1.2
    WORD_LENGTH = 6
    INJECT_RANDOM_WORD_INTERVAL = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _generate_random_word(self, rng: np.random.Generator, length: int) -> str:
        """Generates a random word of specified length using lowercase letters."""
        letters = string.ascii_lowercase
        return "".join(rng.choice(list(letters), size=length))

    # --- Perlin Noise Generation Functions (Adapted from user input) ---
    def _interpolant(self, t):
        # Equivalent to: t*t*t*(t*(t*6 - 15) + 10)
        # Uses numpy operations for potential array input
        return np.power(t, 3) * (t * (t * 6 - 15) + 10)

    def _generate_perlin_noise_2d(
        self, rng: np.random.Generator, shape, res, tileable=(False, False)
    ):
        """Generate a 2D numpy array of perlin noise."""
        delta = (res[0] / shape[0], res[1] / shape[1])
        d = (shape[0] // res[0], shape[1] // res[1])
        grid = np.mgrid[0 : res[0] : delta[0], 0 : res[1] : delta[1]].transpose(1, 2, 0) % 1
        # Gradients
        angles = 2 * np.pi * rng.random((res[0] + 1, res[1] + 1))  # Use provided rng
        gradients = np.dstack((np.cos(angles), np.sin(angles)))
        if tileable[0]:
            gradients[-1, :] = gradients[0, :]
        if tileable[1]:
            gradients[:, -1] = gradients[:, 0]
        gradients = gradients.repeat(d[0], 0).repeat(d[1], 1)
        g00 = gradients[: -d[0], : -d[1]]
        g10 = gradients[d[0] :, : -d[1]]
        g01 = gradients[: -d[0], d[1] :]
        g11 = gradients[d[0] :, d[1] :]
        # Ramps
        n00 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1])) * g00, 2)
        n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
        n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
        n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
        # Interpolation
        t = self._interpolant(grid)  # Use the class method
        n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
        n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
        # Scale output to roughly [-1, 1]
        # The factor sqrt(2) scales the output range closer to [-1, 1]
        # Empirically, Perlin noise often falls within [-sqrt(N/4), sqrt(N/4)] where N is dimensions (2 here)
        # So sqrt(2) scaling is appropriate for 2D.
        return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)

    def _generate_fractal_noise_2d(
        self,
        rng: np.random.Generator,
        shape,
        res,
        octaves=1,
        persistence=0.5,
        lacunarity=2,
        tileable=(False, False),
    ):
        """Generate a 2D numpy array of fractal noise."""
        noise = np.zeros(shape)
        frequency = 1
        amplitude = 1
        for _ in range(octaves):
            # Ensure resolution is integer for the perlin function
            current_res = (int(frequency * res[0]), int(frequency * res[1]))
            # Check if shape is multiple of current_res * lacunarity factor implicitly handled by perlin function's grid calculation
            # We adjusted shape beforehand to be multiple of the highest frequency resolution factor
            noise += amplitude * self._generate_perlin_noise_2d(
                rng,
                shape,
                current_res,
                tileable,  # Pass rng
            )
            frequency *= lacunarity
            amplitude *= persistence

        # Normalize noise to be roughly within [-1, 1]
        # The theoretical max amplitude is sum(persistence^i for i in 0..octaves-1)
        # But practically, it rarely reaches that. Normalizing by max absolute value is safer.
        max_abs_noise = np.max(np.abs(noise))
        if max_abs_noise > 1e-6:  # Avoid division by zero
            noise /= max_abs_noise

        return noise

    # --- End Perlin Noise ---

    def _generate_image_like_data(self, rng: np.random.Generator, target_size: int) -> bytes:
        """Generates byte data using Perlin noise."""
        if target_size <= 0:
            return b""

        # Determine base shape
        width = max(1, int(math.sqrt(target_size)))
        height = max(1, math.ceil(target_size / width))

        # Adjust shape to be multiple of factor required by fractal noise
        # factor = lacunarity**(octaves-1) * res
        factor_x = int(self.PERLIN_LACUNARITY ** (self.PERLIN_OCTAVES - 1) * self.PERLIN_RES[0])
        factor_y = int(self.PERLIN_LACUNARITY ** (self.PERLIN_OCTAVES - 1) * self.PERLIN_RES[1])
        # Ensure factors are at least 1
        factor_x = max(1, factor_x)
        factor_y = max(1, factor_y)

        height_adj = max(
            factor_y, math.ceil(height / factor_y) * factor_y
        )  # Ensure at least factor_y
        width_adj = max(
            factor_x, math.ceil(width / factor_x) * factor_x
        )  # Ensure at least factor_x

        shape = (height_adj, width_adj)
        logging.debug(f"Generating Perlin noise with adjusted shape: {shape}")

        # Generate fractal noise in range [-1, 1]
        noise = self._generate_fractal_noise_2d(
            rng=rng,  # Pass the generator
            shape=shape,
            res=self.PERLIN_RES,
            octaves=self.PERLIN_OCTAVES,
            persistence=self.PERLIN_PERSISTENCE,
            lacunarity=self.PERLIN_LACUNARITY,
            tileable=(False, False),
        )

        # Scale noise from [-1, 1] to [0, 255]
        scaled_noise = (noise + 1) * 0.5 * 255

        # Convert to bytes
        byte_array = np.clip(np.round(scaled_noise), 0, 255).astype(np.uint8)

        # Get bytes and trim to target size
        all_bytes = byte_array.tobytes()
        return all_bytes[:target_size]

    def _generate_text_like_data(self, rng: np.random.Generator, target_size: int) -> bytes:
        """Generates text data using random words and Zipf distribution."""
        if target_size <= 0:
            return b""

        # Generate vocabulary
        vocabulary = [
            self._generate_random_word(rng, self.WORD_LENGTH) for _ in range(self.VOCABULARY_SIZE)
        ]
        vocab_bytes = [word.encode("utf-8") for word in vocabulary]
        space_byte = b" "

        generated_words = []
        current_byte_length = 0
        word_count = 0

        progress_made_in_last_iteration = True
        while current_byte_length < target_size and progress_made_in_last_iteration:
            progress_made_in_last_iteration = False
            remaining_size = target_size - current_byte_length
            batch_estimate = max(1, math.ceil(remaining_size / (self.WORD_LENGTH + 1)))
            word_indices_batch = rng.zipf(self.ZIPF_PARAMETER_A, size=batch_estimate)
            word_indices_batch = np.clip(word_indices_batch, 1, self.VOCABULARY_SIZE) - 1

            for idx in word_indices_batch:
                # Inject random word
                if word_count > 0 and word_count % self.INJECT_RANDOM_WORD_INTERVAL == 0:
                    random_word_str = self._generate_random_word(rng, self.WORD_LENGTH)
                    random_word_byte = random_word_str.encode("utf-8")
                    added_length_random = len(random_word_byte) + (
                        1 if generated_words else 0
                    )  # Add space
                    if current_byte_length + added_length_random <= target_size:
                        generated_words.append(random_word_byte)
                        current_byte_length += added_length_random
                        progress_made_in_last_iteration = True
                    else:
                        break  # Inner loop

                if current_byte_length >= target_size:
                    break  # Inner loop

                # Add vocab word
                word_byte = vocab_bytes[idx]
                added_length_vocab = len(word_byte) + (1 if generated_words else 0)  # Add space
                if current_byte_length + added_length_vocab <= target_size:
                    generated_words.append(word_byte)
                    current_byte_length += added_length_vocab
                    word_count += 1
                    progress_made_in_last_iteration = True
                else:
                    break  # Inner loop

            if not generated_words and target_size <= 0:
                break  # Outer loop safety

        return space_byte.join(generated_words)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate binary data for the gzip compression task, combining image-like
        and text-like data characteristics.

        Approximately half the data has spatial correlation (image-like), and
        the other half consists of random words sampled via Zipf distribution
        with periodic random word injection (text-like).

        Args:
            n (int): Scaling parameter, determines the target plaintext size.
            random_seed (int): Seed for reproducibility.

        Returns:
            dict: A dictionary containing the problem parameters (plaintext).
        """
        # Use n to scale the target plaintext size
        target_plaintext_size = max(0, n * self.DEFAULT_PLAINTEXT_MULTIPLIER)

        logging.debug(
            f"Generating Gzip compression problem (mixed data) with n={n} "
            f"(target_plaintext_size={target_plaintext_size}), random_seed={random_seed}"
        )

        if target_plaintext_size == 0:
            logging.debug("Target size is 0, returning empty bytes.")
            return {"plaintext": b""}

        # Seed the numpy random number generator for reproducibility
        rng = np.random.default_rng(random_seed)

        # Split target size (roughly 50/50)
        image_target_size = target_plaintext_size // 2
        text_target_size = target_plaintext_size - image_target_size

        logging.debug(f"Target sizes: Image-like={image_target_size}, Text-like={text_target_size}")

        # Generate image-like data
        image_bytes = self._generate_image_like_data(rng, image_target_size)
        logging.debug(f"Generated image-like data size: {len(image_bytes)} bytes")

        # Generate text-like data
        text_bytes = self._generate_text_like_data(rng, text_target_size)
        logging.debug(f"Generated text-like data size: {len(text_bytes)} bytes")

        # Combine the data
        plaintext_bytes = image_bytes + text_bytes

        # Log final size
        logging.debug(f"Generated final combined plaintext size: {len(plaintext_bytes)} bytes")

        return {
            "plaintext": plaintext_bytes,
        }

    def solve(self, problem: dict[str, Any]) -> dict[str, bytes]:
        """
        Compress the plaintext using the gzip algorithm with mtime=0.

        Args:
            problem (dict): The problem dictionary generated by `generate_problem`.

        Returns:
            dict: A dictionary containing 'compressed_data'.
        """
        plaintext = problem["plaintext"]

        try:
            # Compress the data using gzip, setting compresslevel=9 and mtime=0 for deterministic output
            compressed_data = gzip.compress(plaintext, compresslevel=9, mtime=0)
            return {"compressed_data": compressed_data}

        except Exception as e:
            logging.error(f"Error during gzip compression in solve: {e}")
            raise  # Re-raise exception

    def is_solution(self, problem: dict[str, Any], solution: dict[str, bytes] | Any) -> bool:
        """
        Verify the provided gzip compression solution.

        Checks:
        1. The solution format is valid (dict with 'compressed_data' as bytes).
        2. Decompressing the solution's data yields the original plaintext.
        3. The length of the compressed data in the solution is at most
           machine epsilon larger than the length produced by self.solve().

        Args:
            problem (dict): The problem dictionary.
            solution (dict): The proposed solution dictionary with 'compressed_data'.

        Returns:
            bool: True if the solution is valid and meets the criteria.
        """
        if not isinstance(solution, dict) or "compressed_data" not in solution:
            logging.error(
                f"Invalid solution format. Expected dict with 'compressed_data'. Got: {type(solution)}"
            )
            return False

        compressed_data = solution["compressed_data"]
        if not isinstance(compressed_data, bytes):
            logging.error("Solution 'compressed_data' is not bytes.")
            return False

        original_plaintext = problem.get("plaintext")
        if original_plaintext is None:
            logging.error("Problem dictionary missing 'plaintext'. Cannot verify.")
            return False  # Cannot verify without original data

        # 1. Check if decompression yields the original input
        try:
            decompressed_data = gzip.decompress(compressed_data)
        except Exception as e:
            logging.error(f"Failed to decompress solution data: {e}")
            return False

        if decompressed_data != original_plaintext:
            logging.error("Decompressed data does not match original plaintext.")
            # Log lengths for debugging
            logging.debug(
                f"Original length: {len(original_plaintext)}, Decompressed length: {len(decompressed_data)}"
            )
            # Log first/last few bytes if lengths match but content differs
            if len(decompressed_data) == len(original_plaintext):
                logging.debug(
                    f"Original start: {original_plaintext[:50]}, Decompressed start: {decompressed_data[:50]}"
                )
                logging.debug(
                    f"Original end: {original_plaintext[-50:]}, Decompressed end: {decompressed_data[-50:]}"
                )
            return False

        # 2. Check if the compressed size is close to the reference solution size
        #    Generate reference solution using the same compression settings.
        try:
            # reference_solution = self.solve(problem) # Use direct compression here to avoid recursion if solve changes
            reference_compressed_data = gzip.compress(original_plaintext, compresslevel=9, mtime=0)
        except Exception as e:
            logging.error(f"Failed to generate reference solution in is_solution: {e}")
            # Cannot verify size constraint if reference generation fails
            return False

        solution_len = len(compressed_data)
        reference_len = len(reference_compressed_data)

        # Allow solution length to be at most 0.1% larger than reference length.
        # Calculate the maximum allowed length (reference + 0.1%)
        # Use math.ceil to allow the integer length to reach the ceiling of the limit.
        max_allowed_len = math.ceil(reference_len * 1.001)

        # Calculate compression ratios for logging
        # original_len = len(original_plaintext)
        # Avoid division by zero if original_plaintext is empty
        # ref_ratio = (reference_len / original_len) if original_len > 0 else float('inf')
        # sol_ratio = (solution_len / original_len) if original_len > 0 else float('inf')


        if solution_len > max_allowed_len:
            logging.error(
                f"Compressed data length ({solution_len}) is more than 0.1% larger than reference length ({reference_len}). Max allowed: {max_allowed_len}."
            )
            return False

        # All checks passed
        return True