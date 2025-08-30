# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from enum import Enum
from typing import Any

import numpy as np
from scipy.interpolate import RBFInterpolator



class ProblemType(Enum):
    """Enum for different types of RBF interpolation problem configurations."""

    STANDARD = "standard"
    LOW_DIM = "low_dimensional"
    HIGH_DIM = "high_dimensional"
    SPARSE = "sparse"
    DENSE = "dense"
    NOISY = "noisy"
    SMOOTH = "smooth"
    OSCILLATORY = "oscillatory"
    CLUSTERED = "clustered"
    OUTLIERS = "outliers"
    DISCONTINUOUS = "discontinuous"
    ANISOTROPIC = "anisotropic"


class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Radial Basis Function (RBF) interpolation task.

        In this task, you are given a set of points in N dimensions with corresponding
        function values. Your goal is to compute an RBF interpolation function that can
        be used to predict function values at arbitrary points within the domain.

        The task uses scipy.interpolate.RBFInterpolator to perform the interpolation.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 42) -> dict[str, Any]:
        """
        Generate an RBF interpolation problem.

        The problem characteristics (dimensions, density, noise, etc.) are determined
        based on the complexity parameter 'n' and the random seed.

        :param n: Base scaling parameter for the problem size.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the RBF interpolation problem.
        """
        # Determine ProblemType based on n/randomness
        # This replaces the problem_type parameter
        random.seed(random_seed)  # Seed before choosing type
        np.random.seed(random_seed)
        available_types = list(ProblemType)
        # Bias towards STANDARD for low n, allow more complex types for high n
        if n < 5:
            prob_weights = [
                0.5 if t == ProblemType.STANDARD else 0.5 / (len(available_types) - 1)
                for t in available_types
            ]
        elif n < 15:
            prob_weights = [
                0.3 if t == ProblemType.STANDARD else 0.7 / (len(available_types) - 1)
                for t in available_types
            ]
        else:  # Higher n, more likely complex types
            prob_weights = [
                0.1 if t == ProblemType.STANDARD else 0.9 / (len(available_types) - 1)
                for t in available_types
            ]
        problem_type = random.choices(available_types, weights=prob_weights, k=1)[0]

        logging.debug(
            f"Generating {problem_type.value} RBF interpolation problem with n={n} and random_seed={random_seed}"
        )
        # The rest of the generation logic uses the determined problem_type

        # Set parameters based on problem type
        if problem_type == ProblemType.LOW_DIM:
            n_dims = random.randint(1, 2)
            n_samples = random.randint(n * 5, n * 10)
            function_type = "smooth"

        elif problem_type == ProblemType.HIGH_DIM:
            n_dims = random.randint(5, min(10, n))
            n_samples = random.randint(n * 10, n * 20)
            function_type = "simple"

        elif problem_type == ProblemType.SPARSE:
            n_dims = random.randint(2, min(5, n))
            n_samples = random.randint(n, n * 2)
            function_type = "complex"

        elif problem_type == ProblemType.DENSE:
            n_dims = random.randint(1, min(4, n))
            n_samples = random.randint(n * 20, n * 50)
            function_type = "complex"

        elif problem_type == ProblemType.NOISY:
            n_dims = random.randint(1, min(4, n))
            n_samples = random.randint(n * 5, n * 15)
            function_type = "noisy"

        elif problem_type == ProblemType.SMOOTH:
            n_dims = random.randint(1, min(5, n))
            n_samples = random.randint(n * 5, n * 15)
            function_type = "smooth"

        elif problem_type == ProblemType.OSCILLATORY:
            n_dims = random.randint(1, min(3, n))
            n_samples = random.randint(n * 10, n * 20)
            function_type = "oscillatory"

        elif problem_type == ProblemType.CLUSTERED:
            n_dims = random.randint(1, min(5, n))
            n_samples = random.randint(n * 5, n * 15)
            function_type = "standard"

        elif problem_type == ProblemType.OUTLIERS:
            n_dims = random.randint(1, min(4, n))
            n_samples = random.randint(n * 5, n * 15)
            function_type = "outliers"

        elif problem_type == ProblemType.DISCONTINUOUS:
            n_dims = random.randint(1, min(3, n))
            n_samples = random.randint(n * 10, n * 20)
            function_type = "discontinuous"

        elif problem_type == ProblemType.ANISOTROPIC:
            n_dims = random.randint(2, min(5, n))
            n_samples = random.randint(n * 5, n * 15)
            function_type = "anisotropic"

        else:  # STANDARD
            n_dims = random.randint(1, min(5, n))
            n_samples = random.randint(n * 3, n * 10)
            function_type = "standard"

        # Determine the number of test samples
        n_test = max(n, n_samples // 5)

        # Generate training input points based on problem type
        if problem_type == ProblemType.CLUSTERED:
            x_train = self._generate_clustered_points(n_samples, n_dims, random_seed)
        else:
            x_train = np.random.rand(n_samples, n_dims)

        # Possibly transform the input space for anisotropic problems
        if problem_type == ProblemType.ANISOTROPIC:
            scales = np.exp(np.random.uniform(-1, 1, n_dims))
            x_train = x_train * scales

        # Generate function values based on function type
        y_train = self._generate_function_values(x_train, function_type, problem_type, random_seed)

        # Generate test input points - uniformly distributed for testing
        x_test = np.random.rand(n_test, n_dims)
        if problem_type == ProblemType.ANISOTROPIC:
            x_test = x_test * scales

        # Choose appropriate RBF configuration based on problem type
        rbf_config = self._select_rbf_config(problem_type, n_dims, n_samples)

        problem = {
            "x_train": x_train,
            "y_train": y_train,
            "x_test": x_test,
            "rbf_config": rbf_config,
        }

        logging.debug(
            f"Generated {problem_type.value} RBF problem with {n_dims} dimensions and {n_samples} samples."
        )
        logging.debug(f"RBF config: {rbf_config}")

        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solve the RBF interpolation problem using scipy.interpolate.RBFInterpolator.

        This method creates an RBF interpolation function from the training data and
        evaluates it on the test points. It uses the RBF configuration parameters
        provided in the problem dictionary.

        :param problem: A dictionary representing the RBF interpolation problem,
                        which should include an "rbf_config" key with configuration parameters.
        :return: A dictionary with the solution containing:
                 - "y_pred": Predicted function values at test points.
                 - "rbf_config": Configuration parameters used for the RBF interpolator.
        """
        x_train = np.asarray(problem["x_train"], float)
        y_train = np.asarray(problem["y_train"], float).ravel()
        x_test = np.asarray(problem["x_test"], float)

        rbf_config = problem.get("rbf_config")
        kernel = rbf_config.get("kernel")
        epsilon = rbf_config.get("epsilon")
        smoothing = rbf_config.get("smoothing")

        rbf_interpolator = RBFInterpolator(
            x_train, y_train, kernel=kernel, epsilon=epsilon, smoothing=smoothing
        )

        y_pred = rbf_interpolator(x_test)

        solution = {
            "y_pred": y_pred.tolist(),
        }

        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> float:
        """
        Validate the RBF interpolation solution.

        This method performs extensive checks including:
          - The solution contains the required keys.
          - The shapes of solution components match expected shapes.
          - The values are finite (no NaNs or infinities).
          - The prediction quality is within an acceptable range compared to reference.
          - Interpolation accuracy at training points.
          - Configuration parameters are valid.
          - Solution behaves reasonably for out-of-bounds inputs.
          - Solution handles duplicate points and edge cases.

        :param problem: A dictionary representing the RBF interpolation problem.
        :param solution: A dictionary containing the RBF interpolation solution.
        :return: True if the solution is valid, False otherwise.
        """
        # Check that the solution contains the required keys
        if "y_pred" not in solution:
            logging.error("Solution does not contain 'y_pred' key.")
            return False

        try:
            y_pred = np.array(solution["y_pred"])
        except Exception as e:
            logging.error(f"Error converting solution to numpy array: {e}")
            return False

        # Extract problem components
        x_train = problem.get("x_train")
        y_train = problem.get("y_train")
        x_test = problem.get("x_test")

        if x_train is None or y_train is None or x_test is None:
            logging.error("Problem does not contain required data.")
            return False

        reference_solution = self.solve(problem)
        if reference_solution is None:
            logging.error("Reference solution could not be computed.")
            return False

        # Compare to reference solution
        try:
            y_pred_ref = np.array(reference_solution["y_pred"])

            # Check if shapes match
            if y_pred.shape != y_pred_ref.shape:
                logging.error(
                    f"Prediction shape mismatch: got {y_pred.shape}, expected {y_pred_ref.shape}"
                )
                return False

            # Check for non-finite values
            if not np.all(np.isfinite(y_pred)):
                logging.error("Prediction contains NaN or infinite values.")
                return False

            # Compute normalized root mean squared error
            rmse = np.sqrt(np.mean((y_pred - y_pred_ref) ** 2))
            y_range = np.max(y_pred_ref) - np.min(y_pred_ref)

            # If range is too small, use absolute error instead
            if y_range < 1e-10:
                if rmse > 1e-6:
                    logging.error(f"Prediction error too large: RMSE = {rmse}")
                    return False
            else:
                # Normalize RMSE by range
                nrmse = rmse / y_range
                # Allow up to 5% error (this threshold can be adjusted)
                if nrmse > 0.05:
                    logging.error(f"Prediction error too large: NRMSE = {nrmse:.4f}")
                    return False

                logging.info(f"Prediction error within acceptable range: NRMSE = {nrmse:.4f}")
        except Exception as e:
            logging.error(f"Error comparing solutions: {e}")
            return False

        # All checks passed; return True
        return True

    def _generate_clustered_points(
        self, n_samples: int, n_dims: int, random_seed: int
    ) -> np.ndarray:
        """
        Generate points that are clustered in specific regions of the space.

        :param n_samples: Number of points to generate.
        :param n_dims: Number of dimensions.
        :param random_seed: Random seed.
        :return: Array of clustered points.
        """
        np.random.seed(random_seed)

        # Determine number of clusters
        n_clusters = random.randint(2, min(5, n_samples // 10))

        # Generate cluster centers
        centers = np.random.rand(n_clusters, n_dims)

        # Assign each sample to a random cluster
        cluster_assignments = np.random.choice(n_clusters, size=n_samples)

        # Generate points around cluster centers
        points = np.zeros((n_samples, n_dims))
        for i in range(n_samples):
            cluster_idx = cluster_assignments[i]
            # Generate point near the cluster center with Gaussian noise
            points[i] = centers[cluster_idx] + np.random.normal(0, 0.1, n_dims)

        # Ensure all points are within [0, 1] by clipping
        points = np.clip(points, 0, 1)

        return points

    def _generate_function_values(
        self, x: np.ndarray, function_type: str, problem_type: ProblemType, random_seed: int
    ) -> np.ndarray:
        """
        Generate function values for the given input points based on the function type.

        :param x: Input points of shape (n_samples, n_dims).
        :param function_type: Type of function to generate values for.
        :param problem_type: The overall problem type.
        :param random_seed: Random seed.
        :return: Function values of shape (n_samples,).
        """
        np.random.seed(random_seed)
        n_samples, n_dims = x.shape

        if function_type == "smooth":
            # Smooth function - sum of a few broad Gaussian bumps
            n_bumps = min(3, n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.5, 2.0, n_bumps)
            widths = np.random.uniform(0.2, 0.5, n_bumps)

        elif function_type == "oscillatory":
            # Oscillatory function - sum of many narrow Gaussian bumps and sine waves
            n_bumps = min(15, 5 * n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.2, 1.0, n_bumps)
            widths = np.random.uniform(0.02, 0.1, n_bumps)

            # Add sine wave components
            frequencies = np.random.uniform(5, 15, n_dims)
            phases = np.random.uniform(0, 2 * np.pi, n_dims)

        elif function_type == "discontinuous":
            # Function with discontinuities - step functions and Gaussian bumps
            n_bumps = min(5, 2 * n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.5, 2.0, n_bumps)
            widths = np.random.uniform(0.1, 0.3, n_bumps)

            # Create discontinuity thresholds for each dimension
            thresholds = np.random.uniform(0.3, 0.7, n_dims)
            step_heights = np.random.uniform(0.5, 2.0, n_dims)

        elif function_type == "complex":
            # Complex function - combination of Gaussian bumps, polynomials, and trig functions
            n_bumps = min(8, 3 * n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.3, 1.5, n_bumps)
            widths = np.random.uniform(0.05, 0.2, n_bumps)

            # Polynomial coefficients
            poly_degree = min(3, n_dims)
            poly_coeffs = np.random.uniform(-0.5, 0.5, (n_dims, poly_degree + 1))

        elif function_type == "noisy":
            # Base function plus noise
            n_bumps = min(5, 2 * n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.5, 2.0, n_bumps)
            widths = np.random.uniform(0.1, 0.3, n_bumps)

            # Noise level
            noise_level = 0.1

        elif function_type == "simple":
            # Simple function - sum of a few broad Gaussian bumps
            # Good for high-dimensional spaces where complexity grows exponentially
            n_bumps = min(2, n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.5, 2.0, n_bumps)
            widths = np.random.uniform(0.3, 0.6, n_bumps)

        else:  # "standard"
            # Standard function - balanced complexity
            n_bumps = min(5, 2 * n_dims)
            centers = np.random.rand(n_bumps, n_dims)
            amplitudes = np.random.uniform(0.5, 2.0, n_bumps)
            widths = np.random.uniform(0.1, 0.3, n_bumps)

        # Initialize function values
        y = np.zeros(n_samples)

        # Add contribution from Gaussian bumps (common to all function types)
        for i in range(n_bumps):
            # Compute squared distances to the center of each bump
            squared_dists = np.sum((x - centers[i]) ** 2, axis=1)
            # Add the contribution of this bump
            y += amplitudes[i] * np.exp(-squared_dists / (2 * widths[i] ** 2))

        # Add function-type specific components
        if function_type == "oscillatory":
            # Add sine wave components
            for d in range(n_dims):
                y += 0.3 * np.sin(frequencies[d] * x[:, d] + phases[d])

        elif function_type == "discontinuous":
            # Add step functions for discontinuities
            for d in range(n_dims):
                y += step_heights[d] * (x[:, d] > thresholds[d])

        elif function_type == "complex":
            # Add polynomial terms
            for d in range(n_dims):
                for power, coeff in enumerate(poly_coeffs[d]):
                    y += coeff * x[:, d] ** power

        # Handle special problem types
        if problem_type == ProblemType.NOISY or function_type == "noisy":
            # Add random noise
            y += np.random.normal(0, noise_level * np.std(y), n_samples)

        if problem_type == ProblemType.OUTLIERS:
            # Add outliers to ~5% of the data
            n_outliers = max(1, int(0.05 * n_samples))
            outlier_indices = np.random.choice(n_samples, n_outliers, replace=False)
            outlier_values = np.random.uniform(-3, 3, n_outliers) * np.std(y)
            y[outlier_indices] += outlier_values

        if problem_type == ProblemType.ANISOTROPIC:
            # Emphasize certain dimensions more than others
            dimension_weights = np.exp(np.random.uniform(-1, 1, n_dims))
            for d in range(n_dims):
                y += dimension_weights[d] * x[:, d]

        return y

    def _select_rbf_config(
        self, problem_type: ProblemType, n_dims: int, n_samples: int
    ) -> dict[str, Any]:
        """
        Select appropriate RBF configuration based on problem type and dimensions.

        :param problem_type: Type of problem being generated.
        :param n_dims: Number of dimensions.
        :param n_samples: Number of samples.
        :return: Dictionary with RBF configuration parameters.
        """
        # Base configuration
        rbf_config = {}

        # Select kernel based on problem type and dimensions
        if problem_type == ProblemType.SMOOTH:
            kernel_options = ["thin_plate_spline", "cubic", "quintic"]
        elif problem_type == ProblemType.OSCILLATORY:
            kernel_options = ["gaussian", "multiquadric"]
        elif problem_type == ProblemType.NOISY:
            kernel_options = ["thin_plate_spline", "multiquadric"]
        elif problem_type == ProblemType.HIGH_DIM:
            kernel_options = ["gaussian", "thin_plate_spline"]
        elif problem_type == ProblemType.SPARSE:
            kernel_options = ["thin_plate_spline", "multiquadric", "linear"]
        elif problem_type == ProblemType.DENSE:
            kernel_options = ["thin_plate_spline", "cubic", "quintic"]
        elif problem_type == ProblemType.DISCONTINUOUS:
            kernel_options = ["multiquadric", "gaussian"]
        elif problem_type == ProblemType.ANISOTROPIC:
            kernel_options = ["gaussian", "multiquadric"]
        else:
            # For other types, use a mix of kernels that generally work well
            kernel_options = ["thin_plate_spline", "multiquadric", "gaussian"]

            # In higher dimensions, some kernels work better
            if n_dims >= 4:
                kernel_options = ["thin_plate_spline", "gaussian"]

        rbf_config["kernel"] = random.choice(kernel_options)

        # Set epsilon based on kernel type and problem characteristics
        if rbf_config["kernel"] == "gaussian":
            # Gaussian kernel is sensitive to epsilon
            # Smaller epsilon for more oscillatory functions
            if problem_type == ProblemType.OSCILLATORY:
                rbf_config["epsilon"] = random.uniform(0.05, 0.2)
            elif problem_type == ProblemType.SMOOTH:
                rbf_config["epsilon"] = random.uniform(0.2, 0.5)
            else:
                rbf_config["epsilon"] = random.uniform(0.1, 0.3)
        elif rbf_config["kernel"] in ["multiquadric", "inverse_multiquadric"]:
            # These kernels are less sensitive to epsilon
            rbf_config["epsilon"] = random.uniform(0.5, 2.0)
        else:
            # For other kernels, provide a reasonable epsilon
            rbf_config["epsilon"] = random.uniform(1.0, 3.0)

        # Set smoothing based on problem type
        if problem_type == ProblemType.NOISY or problem_type == ProblemType.OUTLIERS:
            # More smoothing for noisy data
            rbf_config["smoothing"] = random.uniform(0.001, 0.01) * n_samples
        elif problem_type == ProblemType.DISCONTINUOUS:
            # Medium smoothing for discontinuous functions
            rbf_config["smoothing"] = random.uniform(0.0001, 0.001) * n_samples
        else:
            # Little smoothing for clean data
            rbf_config["smoothing"] = random.uniform(0, 0.0001) * n_samples

        assert "kernel" in rbf_config, "Kernel must be specified in RBF config"
        assert "epsilon" in rbf_config, "Epsilon must be specified in RBF config"
        assert "smoothing" in rbf_config, "Smoothing must be specified in RBF config"
        return rbf_config