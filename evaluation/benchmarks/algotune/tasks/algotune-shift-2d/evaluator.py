# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import numpy as np
import scipy.ndimage



def _is_empty(x):
    if x is None:
        return True
    if isinstance(x, np.ndarray):
        return x.size == 0
    try:
        return len(x) == 0
    except TypeError:
        return False


class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Shift2D task.

        Shifts a 2D image by a given vector using scipy.ndimage.shift.
        Uses cubic spline interpolation (order=3) and 'constant' mode.
        The shift is applied along each axis.
        """
        super().__init__(**kwargs)
        self.order = 3
        self.mode = "constant"

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generates a 2D shift problem.

        Creates a random 2D array (image) of size n x n and a 2-element shift vector.

        :param n: The side dimension of the square input image.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the problem with keys:
                 "image": Input image as a numpy array (n x n).
                 "shift": The shift vector [shift_row, shift_col] (numpy array).
        """
        logging.debug(f"Generating 2D Shift problem with n={n}, random_seed={random_seed}")
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Generate random n x n image
        image = np.random.rand(n, n) * 255.0

        # Generate a random shift vector (e.g., up to 10% of dimension)
        max_shift = n * 0.1
        shift_vector = np.random.uniform(-max_shift, max_shift, size=2)

        problem = {"image": image, "shift": shift_vector}
        logging.debug(f"Generated 2D Shift problem for image shape ({n},{n}), shift={shift_vector}")
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solves the 2D shift problem using scipy.ndimage.shift.

        :param problem: A dictionary representing the problem.
        :return: A dictionary with key "shifted_image":
                 "shifted_image": The shifted image as an array.
        """
        image = problem["image"]
        shift_vector = problem["shift"]

        try:
            shifted_image = scipy.ndimage.shift(
                image, shift_vector, order=self.order, mode=self.mode
            )
        except Exception as e:
            logging.error(f"scipy.ndimage.shift failed: {e}")
            return {"shifted_image": []}  # Indicate failure

        solution = {"shifted_image": shifted_image}
        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Check if the provided shift solution is valid.

        Checks structure, dimensions, finite values, and numerical closeness to
        the reference scipy.ndimage.shift output.

        :param problem: The problem definition dictionary.
        :param solution: The proposed solution dictionary.
        :return: True if the solution is valid, False otherwise.
        """
        if not all(k in problem for k in ["image", "shift"]):
            logging.error("Problem dictionary missing 'image' or 'shift'.")
            return False
        image = problem["image"]
        shift_vector = problem["shift"]

        if not isinstance(solution, dict) or "shifted_image" not in solution:
            logging.error("Solution format invalid: missing 'shifted_image' key.")
            return False

        proposed_list = solution["shifted_image"]

        # Handle potential failure case
        if _is_empty(proposed_list):
            logging.warning("Proposed solution is empty list (potential failure).")
            try:
                ref_output = scipy.ndimage.shift(
                    image, shift_vector, order=self.order, mode=self.mode
                )
                if ref_output.size == 0:
                    logging.info("Reference solver also produced empty result. Accepting.")
                    return True
                else:
                    logging.error("Reference solver succeeded, but proposed solution was empty.")
                    return False
            except Exception:
                logging.info("Reference solver also failed. Accepting empty solution.")
                return True

        if not isinstance(proposed_list, list):
            logging.error("'shifted_image' is not a list.")
            return False

        try:
            proposed_array = np.array(proposed_list, dtype=float)
        except ValueError:
            logging.error("Could not convert 'shifted_image' list to numpy float array.")
            return False

        # Check shape consistency (should match input)
        if proposed_array.shape != image.shape:
            logging.error(f"Output shape {proposed_array.shape} != input shape {image.shape}.")
            return False

        if not np.all(np.isfinite(proposed_array)):
            logging.error("Proposed 'shifted_image' contains non-finite values.")
            return False

        # Re-compute reference solution
        try:
            ref_array = scipy.ndimage.shift(image, shift_vector, order=self.order, mode=self.mode)
        except Exception as e:
            logging.error(f"Error computing reference solution: {e}")
            return False

        # Compare results
        rtol = 1e-5
        atol = 1e-7
        is_close = np.allclose(proposed_array, ref_array, rtol=rtol, atol=atol)

        if not is_close:
            abs_diff = np.abs(proposed_array - ref_array)
            max_abs_err = np.max(abs_diff) if abs_diff.size > 0 else 0
            logging.error(
                f"Solution verification failed: Output mismatch. "
                f"Max absolute error: {max_abs_err:.3f} (rtol={rtol}, atol={atol})"
            )
            return False

        logging.debug("Solution verification successful.")
        return True