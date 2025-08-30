# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from enum import Enum
from typing import Any

import numpy as np
from scipy import signal



class SignalType(Enum):
    """Enum for different types of signals that can be generated."""

    RANDOM = "random"
    IMPULSE = "impulse"
    STEP = "step"
    SINE = "sine"
    COSINE = "cosine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    GAUSSIAN = "gaussian"
    EXPONENTIAL = "exponential"


class Task:
    def __init__(self, **kwargs):
        """
        Initialize the FFT Convolution task.

        In this task, you are given two signals x and y, and your goal is to compute their convolution
        using the Fast Fourier Transform (FFT). The convolution of x and y is defined as:

            z[n] = sum_k x[k] * y[n-k]

        Using the FFT approach exploits the fact that convolution in the time domain
        is equivalent to multiplication in the frequency domain.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random FFT convolution problem.

        The complexity (signal lengths, types, noise) are determined by 'n'.

        :param n: Base scaling parameter controlling complexity.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the convolution problem.
        """
        logging.debug(f"Generating FFT convolution problem with n={n}, seed={random_seed}")
        random.seed(random_seed)
        np.random.seed(random_seed)

        # --- Determine parameters based on n and random_seed ---

        # Signal lengths based on n
        len_x = random.randint(n, n * 2 + 5)  # Add some base variation
        len_y = random.randint(n, n * 2 + 5)

        # Select signal types (more complex types for higher n)
        available_types = list(SignalType)
        if n < 10:
            possible_types = [
                SignalType.RANDOM,
                SignalType.IMPULSE,
                SignalType.STEP,
                SignalType.SINE,
                SignalType.COSINE,
            ]
        elif n < 50:
            possible_types = [
                t for t in available_types if t not in [SignalType.GAUSSIAN, SignalType.EXPONENTIAL]
            ]
        else:
            possible_types = available_types

        signal_x_type = random.choice(possible_types)
        signal_y_type = random.choice(possible_types)

        # Signal parameters (can be randomized further based on type and n)
        signal_x_params = {"length": len_x}  # Base params
        signal_y_params = {"length": len_y}
        # Example: Add frequency based on n for periodic signals
        if signal_x_type in [
            SignalType.SINE,
            SignalType.COSINE,
            SignalType.SQUARE,
            SignalType.TRIANGLE,
            SignalType.SAWTOOTH,
        ]:
            signal_x_params["frequency"] = random.uniform(1, max(2, n / 10))
        if signal_y_type in [
            SignalType.SINE,
            SignalType.COSINE,
            SignalType.SQUARE,
            SignalType.TRIANGLE,
            SignalType.SAWTOOTH,
        ]:
            signal_y_params["frequency"] = random.uniform(1, max(2, n / 10))
        # Add more randomized parameters based on signal types and n here...
        if signal_x_type == SignalType.GAUSSIAN:
            signal_x_params["sigma"] = len_x / random.uniform(5, 15)
        if signal_y_type == SignalType.GAUSSIAN:
            signal_y_params["sigma"] = len_y / random.uniform(5, 15)

        # Mode
        mode = random.choice(["full", "same", "valid"])

        # Noise (increase probability and level with n)
        add_noise = random.random() < (0.1 + min(0.4, n / 200.0))  # Probability increases with n
        noise_level = random.uniform(0.005, 0.05) * (
            1 + min(2, n / 100.0)
        )  # Level increases with n

        # --- End parameter determination ---

        # Generate signals using derived parameters
        signal_x = self._generate_signal(signal_x_type, len_x, **signal_x_params)
        signal_y = self._generate_signal(signal_y_type, len_y, **signal_y_params)

        if add_noise:
            x_amplitude = np.max(np.abs(signal_x)) if len(signal_x) > 0 else 1.0
            if x_amplitude == 0:
                x_amplitude = 1.0  # Avoid noise level issues with zero signal
            y_amplitude = np.max(np.abs(signal_y)) if len(signal_y) > 0 else 1.0
            if y_amplitude == 0:
                y_amplitude = 1.0

            signal_x += np.random.normal(0, noise_level * x_amplitude, len_x)
            signal_y += np.random.normal(0, noise_level * y_amplitude, len_y)

        problem = {
            "signal_x": signal_x.tolist(),
            "signal_y": signal_y.tolist(),
            "mode": mode,
        }

        logging.debug(
            f"Generated FFT convolution problem (n={n}) with lengths {len_x}, {len_y}, types {signal_x_type.value}, {signal_y_type.value}, mode: {mode}."
        )
        return problem

    def _generate_signal(self, signal_type: SignalType, length_sig: int, **kwargs) -> np.ndarray:
        """
        Generate a signal of the specified type and length.

        :param signal_type: Type of signal to generate.
        :param length_sig: Length of the signal.
        :param kwargs: Additional parameters for specific signal types.
        :return: NumPy array containing the generated signal.
        """
        t = np.linspace(0, kwargs.get("duration", 1), length_sig, endpoint=False)

        if signal_type == SignalType.RANDOM:
            amplitude = kwargs.get("amplitude", 1.0)
            return amplitude * np.random.randn(length_sig)

        elif signal_type == SignalType.IMPULSE:
            position = kwargs.get(
                "position", random.randint(0, length_sig - 1) if length_sig > 0 else 0
            )
            amplitude = kwargs.get("amplitude", 1.0)
            signal_out = np.zeros(length_sig)
            if 0 <= position < length_sig:
                signal_out[position] = amplitude
            return signal_out

        elif signal_type == SignalType.STEP:
            position = kwargs.get(
                "position", random.randint(0, length_sig) if length_sig > 0 else 0
            )
            amplitude = kwargs.get("amplitude", 1.0)
            signal_out = np.zeros(length_sig)
            if position < length_sig:
                signal_out[position:] = amplitude
            return signal_out

        elif signal_type == SignalType.SINE:
            frequency = kwargs.get("frequency", 5.0)
            amplitude = kwargs.get("amplitude", 1.0)
            phase = kwargs.get("phase", random.uniform(0, 2 * np.pi))
            return amplitude * np.sin(2 * np.pi * frequency * t + phase)

        elif signal_type == SignalType.COSINE:
            frequency = kwargs.get("frequency", 5.0)
            amplitude = kwargs.get("amplitude", 1.0)
            phase = kwargs.get("phase", random.uniform(0, 2 * np.pi))
            return amplitude * np.cos(2 * np.pi * frequency * t + phase)

        elif signal_type == SignalType.SQUARE:
            frequency = kwargs.get("frequency", 5.0)
            amplitude = kwargs.get("amplitude", 1.0)
            duty = kwargs.get("duty", random.uniform(0.1, 0.9))
            # Use modulo arithmetic for phase to avoid potential issues with signal.square
            phase_shift = random.uniform(0, 1)  # Phase shift in terms of fraction of a cycle
            return amplitude * signal.square(
                2 * np.pi * frequency * t + phase_shift * 2 * np.pi, duty=duty
            )

        elif signal_type == SignalType.TRIANGLE:
            frequency = kwargs.get("frequency", 5.0)
            amplitude = kwargs.get("amplitude", 1.0)
            # signal.sawtooth with width=0.5 produces a triangle wave
            phase_shift = random.uniform(0, 1)
            return amplitude * signal.sawtooth(
                2 * np.pi * frequency * t + phase_shift * 2 * np.pi, width=0.5
            )

        elif signal_type == SignalType.SAWTOOTH:
            frequency = kwargs.get("frequency", 5.0)
            amplitude = kwargs.get("amplitude", 1.0)
            width = kwargs.get("width", 1.0)  # Controls if it's rising or falling sawtooth
            phase_shift = random.uniform(0, 1)
            return amplitude * signal.sawtooth(
                2 * np.pi * frequency * t + phase_shift * 2 * np.pi, width=width
            )

        elif signal_type == SignalType.GAUSSIAN:
            center = kwargs.get(
                "center", random.uniform(0, length_sig - 1) if length_sig > 0 else 0
            )
            sigma = kwargs.get("sigma", length_sig / random.uniform(5, 15))
            amplitude = kwargs.get("amplitude", 1.0)
            x = np.arange(length_sig)
            # Ensure sigma is reasonably large to avoid numerical issues
            sigma = max(sigma, 0.1)
            return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma**2))

        elif signal_type == SignalType.EXPONENTIAL:
            decay = kwargs.get("decay", random.uniform(1.0, 10.0) / max(1, length_sig))
            amplitude = kwargs.get("amplitude", 1.0)
            is_rising = kwargs.get("rising", random.choice([True, False]))
            if is_rising:
                return amplitude * (1 - np.exp(-decay * np.arange(length_sig)))
            else:
                return amplitude * np.exp(-decay * np.arange(length_sig))

        else:
            logging.warning(f"Unknown signal type {signal_type}, defaulting to random.")
            return np.random.randn(length_sig)

    def solve(self, problem: dict[str, Any]) -> dict[str, list]:
        """
        Solve the convolution problem using the Fast Fourier Transform approach.

        Uses scipy.signal.fftconvolve to compute the convolution of signals x and y.

        :param problem: A dictionary representing the convolution problem.
        :return: A dictionary with key:
                 "convolution": a list representing the convolution result.
        """
        signal_x = np.array(problem["signal_x"])
        signal_y = np.array(problem["signal_y"])
        mode = problem.get("mode", "full")

        # Perform convolution using FFT
        convolution_result = signal.fftconvolve(signal_x, signal_y, mode=mode)

        solution = {"convolution": convolution_result}
        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, list]) -> bool:
        """
        Validate the FFT convolution solution.

        Checks:
        - Solution contains the key 'convolution'.
        - The result is a list of numbers.
        - The result is numerically close to the reference solution computed using scipy.signal.fftconvolve.
        - The length of the result matches the expected length for the given mode.

        :param problem: Dictionary representing the convolution problem.
        :param solution: Dictionary containing the solution with key "convolution".
        :return: True if the solution is valid and accurate, False otherwise.
        """
        if "convolution" not in solution:
            logging.error("Solution missing 'convolution' key.")
            return False

        student_result = solution["convolution"]

        if not isinstance(student_result, list):
            logging.error("Convolution result must be a list.")
            return False

        try:
            student_result_np = np.array(student_result, dtype=float)
            if not np.all(np.isfinite(student_result_np)):
                logging.error("Convolution result contains non-finite values (NaN or inf).")
                return False
        except ValueError:
            logging.error("Could not convert convolution result to a numeric numpy array.")
            return False

        signal_x = np.array(problem["signal_x"])
        signal_y = np.array(problem["signal_y"])
        mode = problem.get("mode", "full")

        # Calculate expected length
        len_x = len(signal_x)
        len_y = len(signal_y)
        if mode == "full":
            expected_len = len_x + len_y - 1
        elif mode == "same":
            expected_len = len_x
        elif mode == "valid":
            expected_len = max(0, max(len_x, len_y) - min(len_x, len_y) + 1)
        else:
            logging.error(f"Invalid mode provided in problem: {mode}")
            return False

        # Handle cases where inputs might be empty
        if len_x == 0 or len_y == 0:
            expected_len = 0

        if len(student_result_np) != expected_len:
            logging.error(
                f"Incorrect result length for mode '{mode}'. "
                f"Expected {expected_len}, got {len(student_result_np)}."
            )
            return False

        # Calculate reference solution
        try:
            reference_result = signal.fftconvolve(signal_x, signal_y, mode=mode)
        except Exception as e:
            logging.error(f"Error calculating reference solution: {e}")
            # Cannot validate if reference calculation fails
            return False

        # Allow for empty result check
        if expected_len == 0:
            if len(student_result_np) == 0:
                return True  # Correct empty result for empty input
            else:
                logging.error("Expected empty result for empty input, but got non-empty result.")
                return False

        # Check numerical closeness
        abs_tol = 1e-6
        rel_tol = 1e-6

        # Explicitly return True/False based on allclose result
        is_close = np.allclose(student_result_np, reference_result, rtol=rel_tol, atol=abs_tol)
        if not is_close:
            diff = np.abs(student_result_np - reference_result)
            max_diff = np.max(diff) if len(diff) > 0 else 0
            avg_diff = np.mean(diff) if len(diff) > 0 else 0
            logging.error(
                f"Numerical difference between student solution and reference exceeds tolerance. "
                f"Max diff: {max_diff:.2e}, Avg diff: {avg_diff:.2e} (atol={abs_tol}, rtol={rel_tol})."
            )
            return False  # Explicitly return False

        return True  # Explicitly return True if all checks passed