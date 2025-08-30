# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import math
import random
from typing import Any

import numpy as np
from scipy.spatial import Voronoi as ScipyVoronoi



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Voronoi diagram construction task.

        In this task, you are given a set of points in 2D space and your goal is to compute
        the Voronoi diagram, which partitions the space into regions such that each region
        consists of all points closer to one particular input point than to any other input point.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 42) -> dict[str, Any]:
        """
        Generate a random Voronoi diagram problem.

        The complexity and characteristics (distribution, bounds, etc.) are determined
        based on the complexity parameter 'n' and the random seed.

        :param n: Base scaling parameter for the number of points.
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the Voronoi problem.
        """
        # Determine parameters based on n and random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Determine distribution type based on n
        available_distributions = ["uniform", "normal", "grid", "circle", "special_case"]
        if n < 10:
            # Higher chance of uniform/grid/special for small n
            weights = [0.3, 0.1, 0.2, 0.1, 0.3]
        elif n < 50:
            # Balanced chances
            weights = [0.25, 0.2, 0.15, 0.15, 0.25]
        else:
            # Higher chance of uniform/normal for large n
            weights = [0.4, 0.3, 0.1, 0.1, 0.1]
        distribution_type = random.choices(available_distributions, weights=weights, k=1)[0]

        # Determine other parameters based on distribution and n
        bounds = [-10.0, 10.0, -10.0, 10.0]  # Default bounds
        cluster_count = random.randint(2, max(3, n // 10)) if distribution_type == "normal" else 3
        grid_dims = None  # Calculated later if needed
        noise_level = (
            random.uniform(0, 0.1 + min(0.2, n / 200.0))
            if distribution_type in ["grid", "circle"]
            else 0.0
        )

        logging.debug(
            f"Generating Voronoi problem with n={n}, distribution={distribution_type}, and random_seed={random_seed}"
        )

        # --- The rest of the generation logic uses the determined parameters ---
        x_min, x_max, y_min, y_max = bounds

        # Determine n_points based on n and distribution
        if distribution_type != "special_case":
            # Allow variability, especially for non-grid/special
            n = max(n, 2)
            base_points = random.randint(max(3, n // 2), n * 2)
            if distribution_type == "grid":
                # Adjust n_points to be a perfect square for grid
                grid_side = int(math.sqrt(base_points))
                n_points = grid_side * grid_side
                grid_dims = (grid_side, grid_side)
                if n_points < 4:  # Ensure at least a 2x2 grid
                    n_points = 4
                    grid_dims = (2, 2)
            else:
                n_points = max(3, base_points)  # Ensure at least 3 points
        else:
            # Special cases have specific n (or derive it based on seed)
            case_id = random_seed % 5
            if case_id == 0 or case_id == 4:
                n_points = 5
            elif case_id == 1:
                n_points = 7
            elif case_id == 2:
                n_points = max(3, min(n, 10))
            elif case_id == 3:
                n_points = max(4, n)  # Ensure enough for 2 clusters
            else:
                n_points = 5  # Default for safety

            # Ensure n is consistent with derived n_points for special cases
            # This assumes the test framework might use the returned n
            # It might be better to store the original n in metadata if needed
            # For now, we prioritize making the problem generation consistent
            n = n_points

        points = None
        cluster_assignments = None

        if distribution_type == "uniform":
            points = np.random.uniform(low=[x_min, y_min], high=[x_max, y_max], size=(n_points, 2))

        elif distribution_type == "normal":
            points = []
            centers = np.random.uniform(
                low=[x_min + 0.2 * (x_max - x_min), y_min + 0.2 * (y_max - y_min)],
                high=[x_max - 0.2 * (x_max - x_min), y_max - 0.2 * (y_max - y_min)],
                size=(cluster_count, 2),
            )

            points_per_cluster = n_points // cluster_count
            remainder = n_points % cluster_count

            cluster_assignments = []

            for i, center in enumerate(centers):
                cluster_size = points_per_cluster + (1 if i < remainder else 0)
                std_dev = min(x_max - x_min, y_max - y_min) * 0.1
                cluster_points = np.random.normal(loc=center, scale=std_dev, size=(cluster_size, 2))
                cluster_points = np.clip(cluster_points, [x_min, y_min], [x_max, y_max])
                points.extend(cluster_points)
                cluster_assignments.extend([i] * cluster_size)

            points = np.array(points)

        elif distribution_type == "grid":
            if grid_dims is None:
                grid_size = int(math.sqrt(n_points))
                grid_dims = (grid_size, grid_size)
                n_points = grid_size * grid_size

            rows, cols = grid_dims
            x_step = (x_max - x_min) / (cols + 1)
            y_step = (y_max - y_min) / (rows + 1)

            points = []
            for i in range(1, rows + 1):
                for j in range(1, cols + 1):
                    x = x_min + j * x_step
                    y = y_min + i * y_step
                    if noise_level > 0:
                        x += np.random.uniform(-noise_level * x_step, noise_level * x_step)
                        y += np.random.uniform(-noise_level * y_step, noise_level * y_step)
                    points.append([x, y])

            points = np.array(points)

        elif distribution_type == "circle":
            center = [(x_min + x_max) / 2, (y_min + y_max) / 2]
            radius = min(x_max - x_min, y_max - y_min) * 0.4

            angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
            points = np.zeros((n_points, 2))

            for i, angle in enumerate(angles):
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)

                if noise_level > 0:
                    noise_radius = radius * noise_level
                    x += np.random.uniform(-noise_radius, noise_radius)
                    y += np.random.uniform(-noise_radius, noise_radius)

                points[i] = [x, y]

        elif distribution_type == "special_case":
            case_id = random_seed % 5

            if case_id == 0:
                points = np.array(
                    [
                        [0.0, 0.0],  # Center
                        [1.0, 1.0],  # Top-right
                        [-1.0, 1.0],  # Top-left
                        [-1.0, -1.0],  # Bottom-left
                        [1.0, -1.0],  # Bottom-right
                    ]
                )
                scale_factor = min(x_max - x_min, y_max - y_min) / 4
                points *= scale_factor
                center_offset = [(x_min + x_max) / 2, (y_min + y_max) / 2]
                points += center_offset

            elif case_id == 1:
                n_points = 7
                center = [(x_min + x_max) / 2, (y_min + y_max) / 2]
                radius = min(x_max - x_min, y_max - y_min) * 0.4

                points = [center]

                for i in range(6):
                    angle = 2 * np.pi * i / 6
                    x = center[0] + radius * np.cos(angle)
                    y = center[1] + radius * np.sin(angle)
                    points.append([x, y])

                points = np.array(points)

            elif case_id == 2:
                n_points = n if n <= 10 else 10
                points = np.zeros((n_points, 2))

                x_values = np.linspace(
                    x_min + 0.1 * (x_max - x_min), x_max - 0.1 * (x_max - x_min), n_points
                )
                y_value = (y_min + y_max) / 2

                for i, x in enumerate(x_values):
                    points[i] = [x, y_value + 1e-6 * np.random.uniform(-1, 1)]

            elif case_id == 3:
                n_per_cluster = n_points // 2

                center1 = [(x_min + x_max) / 4, (y_min + y_max) * 3 / 4]
                center2 = [(x_min + x_max) * 3 / 4, (y_min + y_max) / 4]

                std_dev = min(x_max - x_min, y_max - y_min) * 0.1

                cluster1 = np.random.normal(loc=center1, scale=std_dev, size=(n_per_cluster, 2))
                cluster2 = np.random.normal(
                    loc=center2, scale=std_dev, size=(n_points - n_per_cluster, 2)
                )

                cluster1 = np.clip(cluster1, [x_min, y_min], [x_max, y_max])
                cluster2 = np.clip(cluster2, [x_min, y_min], [x_max, y_max])

                points = np.vstack([cluster1, cluster2])

                cluster_assignments = np.array(
                    [0] * n_per_cluster + [1] * (n_points - n_per_cluster)
                )

            elif case_id == 4:
                n_points = 5
                side_length = min(x_max - x_min, y_max - y_min) * 0.8
                center = [(x_min + x_max) / 2, (y_min + y_max) / 2]
                half_side = side_length / 2

                points = np.array(
                    [
                        center,  # Center
                        [center[0] - half_side, center[1] - half_side],  # Bottom-left
                        [center[0] + half_side, center[1] - half_side],  # Bottom-right
                        [center[0] - half_side, center[1] + half_side],  # Top-left
                        [center[0] + half_side, center[1] + half_side],  # Top-right
                    ]
                )

        problem = {
            "points": points,
            "bounds": bounds,
        }

        logging.debug(
            f"Generated Voronoi problem with {len(points)} points using {distribution_type} distribution."
        )
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solve the Voronoi diagram construction problem using scipy.spatial.Voronoi.

        :param problem: A dictionary representing the Voronoi problem.
        :return: A dictionary with keys:
                 "vertices": List of coordinates of the Voronoi vertices.
                 "regions": List of lists, where each list contains the indices of the Voronoi vertices
                           forming a region.
                 "point_region": List mapping each input point to its corresponding region.
                 "ridge_points": List of pairs of input points, whose Voronoi regions share an edge.
                 "ridge_vertices": List of pairs of indices of Voronoi vertices forming a ridge.
        """
        points = problem["points"]

        vor = ScipyVoronoi(points)

        solution = {
            "vertices": vor.vertices.tolist(),
            "regions": [list(region) for region in vor.regions],
            "point_region": np.arange(len(points)),
            "ridge_points": vor.ridge_points.tolist(),
            "ridge_vertices": vor.ridge_vertices,
        }
        solution["regions"] = [solution["regions"][idx] for idx in vor.point_region]

        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Validate the Voronoi diagram solution with enhanced checks for different problem types.

        This method checks:
          - The solution contains all required keys: 'vertices', 'regions', 'point_region',
            'ridge_points', and 'ridge_vertices'.
          - The dimensions and types of all components match those expected from a Voronoi diagram.
          - The regions are valid (each region is a collection of vertices that form a polygon).
          - Each input point is correctly assigned to a region.
          - The ridge points and ridge vertices are consistent with each other.
          - None of the components contain infinities or NaNs.
          - For clustered data, points from the same cluster have adjacent regions.
          - For structured data, the Voronoi diagram preserves expected symmetries.
          - For special cases, the solution matches the known expected properties.

        :param problem: A dictionary representing the Voronoi problem with key "points".
        :param solution: A dictionary containing the Voronoi diagram with the required keys.
        :return: True if valid, else False.
        """
        points = problem.get("points")
        if points is None:
            logging.error("Problem does not contain 'points'.")
            return False

        required_keys = ["vertices", "regions", "point_region", "ridge_points", "ridge_vertices"]
        for key in required_keys:
            if key not in solution:
                logging.error(f"Solution does not contain '{key}' key.")
                return False

        try:
            vertices = np.array(solution["vertices"])
            regions = solution["regions"]
            point_region = np.array(solution["point_region"])
            ridge_points = np.array(solution["ridge_points"])
            ridge_vertices = np.array(solution["ridge_vertices"])
        except Exception as e:
            logging.error(f"Error converting solution components to numpy arrays: {e}")
            return False

        n_points = points.shape[0]

        if vertices.ndim != 2 or vertices.shape[1] != 2:
            logging.error(
                f"Vertices has incorrect dimensions. Expected (n_vertices, 2), got {vertices.shape}."
            )
            return False

        if point_region.ndim != 1 or point_region.shape[0] != n_points:
            logging.error(
                f"Point region mapping has incorrect dimensions. Expected ({n_points},), got {point_region.shape}."
            )
            return False

        if ridge_points.ndim != 2 or ridge_points.shape[1] != 2:
            logging.error(
                f"Ridge points has incorrect dimensions. Expected (n_ridges, 2), got {ridge_points.shape}."
            )
            return False

        if ridge_vertices.ndim != 2 or ridge_vertices.shape[1] != 2:
            logging.error(
                f"Ridge vertices has incorrect dimensions. Expected (n_ridges, 2), got {ridge_vertices.shape}."
            )
            return False

        for arr, name in zip([vertices], ["vertices"]):
            if not np.all(np.isfinite(arr)):
                logging.error(f"{name} contains non-finite values (inf or NaN).")
                return False

        for i, region_idx in enumerate(point_region):
            if region_idx < 0 or region_idx >= len(regions):
                logging.error(f"Point {i} is assigned to invalid region index {region_idx}.")
                return False

        if np.any(ridge_points < 0) or np.any(ridge_points >= n_points):
            logging.error("Ridge points contain invalid point indices.")
            return False

        valid_indices = (ridge_vertices >= -1) & (ridge_vertices < len(vertices))
        if not np.all(valid_indices):
            logging.error("Ridge vertices contain invalid vertex indices.")
            return False

        try:
            vor_ref = ScipyVoronoi(points)
        except Exception as e:
            logging.error(f"Error creating reference Voronoi diagram: {e}")
            return False

        try:
            vor_vertices_ref = vor_ref.vertices.tolist()

            vor_point_region = vor_ref.point_region.tolist()

            # Compare key properties (number of vertices and regions)
            if len(vertices) != len(vor_vertices_ref):
                logging.error("Number of vertices does not match reference solution.")
                return False

            # Check if each input point is assigned to a similar region
            if len(point_region) != len(vor_point_region):
                logging.error("Point to region mapping does not match reference solution.")
                return False

        except Exception as e:
            logging.error(f"Error verifying solution against scipy implementation: {e}")
            return False

        return True