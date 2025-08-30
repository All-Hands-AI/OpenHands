# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import numpy as np
from scipy.spatial import ConvexHull



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the Convex Hull task.

        In this task, you are given a set of points in 2D space, and your goal is to compute the convex hull,
        which is the smallest convex polygon that contains all the points.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 42) -> dict[str, Any]:
        """
        Generate a random Convex Hull problem.

        The complexity and characteristics (distribution, shape, noise, etc.) are determined
        based on the complexity parameter 'n' and the random seed.

        :param n: Number of points to generate (influences complexity).
        :param random_seed: Seed for reproducibility.
        :return: A dictionary representing the Convex Hull problem.
        """
        # Determine parameters based on n and random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Determine distribution type based on n
        available_distributions = [
            "uniform",
            "normal",
            "grid",
            "circle",
            "clusters",
            "known_simple",
            "known_complex",
        ]
        if n < 10:
            weights = [0.2, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2]  # Favor simple/known for low n
        elif n < 50:
            weights = [0.25, 0.15, 0.15, 0.1, 0.15, 0.1, 0.1]
        else:
            weights = [0.3, 0.2, 0.15, 0.15, 0.1, 0.05, 0.05]  # Favor uniform/normal for high n
        distribution_type = random.choices(available_distributions, weights=weights, k=1)[0]

        # Ensure n is appropriate for known types
        if distribution_type == "known_simple" and n < 4:
            n = 4
        if distribution_type == "known_complex" and n < 10:
            n = 10

        # Determine other parameters based on n and distribution_type
        boundary_points = random.random() < (
            0.3 + min(0.5, n / 100.0)
        )  # Higher chance with more points
        shape = (
            random.choice(["square", "circle", "triangle", "cross"])
            if distribution_type == "uniform"
            else "square"
        )
        noise_level = random.uniform(
            0, 0.05 + min(0.3, n / 200.0)
        )  # Noise increases slightly with n
        outliers = random.randint(0, max(0, n // 10))  # More outliers possible with more points
        cluster_count = random.randint(2, max(3, n // 8)) if distribution_type == "clusters" else 1

        logging.debug(
            f"Generating Convex Hull problem with n={n} points, derived distribution={distribution_type}, "
            f"shape={shape}, noise={noise_level:.2f}, outliers={outliers}, clusters={cluster_count}, seed={random_seed}"
        )

        # --- The rest of the generation logic uses the derived parameters ---
        points = []

        # Generate points based on the distribution type
        if distribution_type == "uniform":
            if shape == "square":
                points = np.random.rand(n, 2)  # Points in [0, 1] x [0, 1]
            elif shape == "circle":
                r = np.sqrt(np.random.rand(n))  # Sqrt for uniform distribution in a circle
                theta = np.random.rand(n) * 2 * np.pi
                points = np.vstack([r * np.cos(theta), r * np.sin(theta)]).T
                points = (points + 1) / 2  # Scale and shift to [0, 1] x [0, 1]
            elif shape == "triangle":
                # Generate points in a unit triangle using barycentric coordinates
                u = np.random.rand(n)
                v = np.random.rand(n)
                mask = u + v > 1  # If u + v > 1, reflect the point
                u[mask] = 1 - u[mask]
                v[mask] = 1 - v[mask]
                points = np.vstack([u, v]).T  # Triangle vertices at (0,0), (1,0), (0,1)
            elif shape == "cross":
                # Generate points in a cross shape
                x = np.random.rand(n)
                y = np.random.rand(n)
                if random.random() < 0.5:
                    x = 0.5 + (x - 0.5) * 0.2  # Concentrate around x=0.5
                else:
                    y = 0.5 + (y - 0.5) * 0.2  # Concentrate around y=0.5
                points = np.vstack([x, y]).T

        elif distribution_type == "normal":
            # Generate points with normal distribution around center
            points = np.random.randn(n, 2) * 0.15 + 0.5
            points = np.clip(points, 0, 1)  # Clip points to stay within [0, 1] x [0, 1]

        elif distribution_type == "grid":
            # Determine grid size based on n
            grid_size = int(np.ceil(np.sqrt(n)))
            x = np.linspace(0, 1, grid_size)
            y = np.linspace(0, 1, grid_size)
            xx, yy = np.meshgrid(x, y)
            grid_points = np.vstack([xx.flatten(), yy.flatten()]).T
            points = grid_points[:n]  # Take the first n points
            # Add some noise to the grid
            points += np.random.randn(*points.shape) * noise_level * 0.1
            points = np.clip(points, 0, 1)  # Clip points to stay within [0, 1] x [0, 1]

        elif distribution_type == "circle":
            # Generate points on a circle
            theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
            radius = 0.4
            x = 0.5 + radius * np.cos(theta)
            y = 0.5 + radius * np.sin(theta)
            points = np.vstack([x, y]).T
            # Add some noise
            points += np.random.randn(*points.shape) * noise_level * radius
            points = np.clip(points, 0, 1)  # Clip points to stay within [0, 1] x [0, 1]

        elif distribution_type == "clusters":
            # Generate cluster centers
            centers = np.random.rand(cluster_count, 2)
            # Assign points to clusters
            points_per_cluster = n // cluster_count
            points = []
            for i in range(cluster_count):
                cluster_points = np.random.randn(points_per_cluster, 2) * 0.1 + centers[i]
                points.append(cluster_points)
            # Add remaining points to a random cluster
            remaining = n - points_per_cluster * cluster_count
            if remaining > 0:
                extra_points = np.random.randn(remaining, 2) * 0.1 + centers[0]
                points.append(extra_points)
            points = np.vstack(points)
            points = np.clip(points, 0, 1)  # Clip points to stay within [0, 1] x [0, 1]

        # Create known simple examples
        elif distribution_type == "known_simple":
            if n >= 4:  # Square
                # Ensure dtype is float to prevent casting errors when adding noise
                points = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]], dtype=float)
                # Fill in with random points if needed
                if n > 4:
                    extra_points = np.random.rand(n - 4, 2) * 0.8 + 0.1  # Inside the square
                    points = np.vstack([points, extra_points])
            # Note: The logic in generate_problem ensures n >= 4 for this type now.

        # Create known complex examples
        elif distribution_type == "known_complex":
            if n >= 10:  # Star-like shape
                angles = np.linspace(0, 2 * np.pi, 10, endpoint=False)
                outer_radius = 0.45
                inner_radius = 0.2
                x = []
                y = []
                for i, angle in enumerate(angles):
                    r = outer_radius if i % 2 == 0 else inner_radius
                    x.append(0.5 + r * np.cos(angle))
                    y.append(0.5 + r * np.sin(angle))
                star_points = np.vstack([x, y]).T
                # Fill with random interior points if needed
                if n > 10:
                    extra_points = []
                    while len(extra_points) < n - 10:
                        point = np.random.rand(2) * 0.8 + 0.1  # Point in [0.1, 0.9] x [0.1, 0.9]
                        # Simple check if it's inside the main circle
                        if (point[0] - 0.5) ** 2 + (point[1] - 0.5) ** 2 < (
                            inner_radius * 1.2
                        ) ** 2:
                            extra_points.append(point)
                    extra_points = np.array(extra_points)
                    points = np.vstack([star_points, extra_points[: n - 10]])
                else:
                    points = star_points[:n]

        # Add boundary points if requested
        if (
            boundary_points
            and n >= 8
            and distribution_type not in ["known_simple", "known_complex"]
        ):
            # Corner points
            corners = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
            # Replace some points with corners
            indices = np.random.choice(len(points), size=min(4, len(points)), replace=False)
            points[indices] = corners

            # Add some edge midpoints if we have enough points
            if n >= 12:
                edges = np.array([[0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5]])
                indices = np.random.choice(len(points), size=min(4, len(points)), replace=False)
                # Make sure we don't overwrite the corners
                for i in range(min(4, len(indices))):
                    if indices[i] not in indices[: min(4, len(points))]:
                        points[indices[i]] = edges[i]

        # Add noise to all points if requested
        if noise_level > 0 and distribution_type not in [
            "grid",
            "circle",
        ]:  # Already added noise for these
            points += np.random.randn(*points.shape) * noise_level * 0.1
            points = np.clip(points, 0, 1)  # Clip points to stay within [0, 1] x [0, 1]

        # Add outliers if requested
        if outliers > 0:
            # Create outliers by placing points far outside the main distribution
            outlier_points = np.random.rand(outliers, 2) * 3 - 1  # Points in [-1, 2] x [-1, 2]
            # Replace some points with outliers
            if len(points) > outliers:
                indices = np.random.choice(len(points), size=outliers, replace=False)
                points[indices] = outlier_points
            else:
                # If we don't have enough points, just add the outliers
                points = np.vstack([points, outlier_points[: len(points)]])

        # Ensure points are unique
        points = np.unique(points, axis=0)

        # If we lost some points due to uniqueness, regenerate them
        while len(points) < n:
            new_points = np.random.rand(n - len(points), 2)
            points = np.vstack([points, new_points])
            points = np.unique(points, axis=0)

        # Ensure we have exactly n points
        # If n was less than 3 initially, this could result in < 3 points
        # points = points[:n]

        # --- Ensure at least 3 points for Convex Hull ---
        min_required = 3
        if len(points) < min_required:
            logging.warning(
                f"Generated fewer than {min_required} unique points ({len(points)}). Adding random points to meet minimum."
            )
            while len(points) < min_required:
                # Add random points, ensuring they are likely unique from existing ones
                new_point = np.random.rand(1, 2)
                # Quick check for exact duplication (unlikely with float, but safe)
                if not np.any(np.all(points == new_point, axis=1)):
                    points = np.vstack([points, new_point])

        # Now ensure we have exactly n points if n >= 3, otherwise we have 3
        if n >= min_required:
            points = points[:n]  # Trim if we added extra to meet min_required but n was larger
        # else: points array already has 3 points

        problem = {
            "points": points,
        }

        logging.debug(f"Generated Convex Hull problem with {len(points)} points.")
        return problem

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        """
        Solve the Convex Hull problem using scipy.spatial.ConvexHull.

        :param problem: A dictionary representing the Convex Hull problem.
        :return: A dictionary with keys:
                 "hull_vertices": List of indices of the points that form the convex hull.
                 "hull_points": List of coordinates of the points that form the convex hull.
        """
        points = problem["points"]
        hull = ConvexHull(points)

        # Get the vertices of the convex hull
        hull_vertices = hull.vertices.tolist()

        # Get the points that form the hull in order
        hull_points = points[hull.vertices].tolist()

        solution = {"hull_vertices": hull_vertices, "hull_points": hull_points}

        return solution

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Validate the Convex Hull solution.

        This method checks:
          - The solution contains the keys 'hull_vertices' and 'hull_points'.
          - The hull_vertices are valid indices into the original points array.
          - The hull_points correspond to the correct points from the original array.
          - The resulting polygon is convex.
          - The hull contains all original points (either inside or on the boundary).

        :param problem: A dictionary representing the Convex Hull problem with key "points".
        :param solution: A dictionary containing the solution with keys "hull_vertices" and "hull_points".
        :return: True if solution is valid, else False.
        """
        points = problem.get("points")
        if points is None:
            logging.error("Problem does not contain 'points'.")
            return False

        # Check that the solution contains the required keys.
        for key in ["hull_vertices", "hull_points"]:
            if key not in solution:
                logging.error(f"Solution does not contain '{key}' key.")
                return False

        try:
            hull_vertices = np.array(solution["hull_vertices"], dtype=int)
            hull_points = np.array(solution["hull_points"])
        except Exception as e:
            logging.error(f"Error converting solution lists to numpy arrays: {e}")
            return False

        # Check that hull_vertices are valid indices
        if np.any(hull_vertices < 0) or np.any(hull_vertices >= len(points)):
            logging.error("Hull vertices contain invalid indices.")
            return False

        # Check that hull_points correspond to the correct points
        if not np.allclose(points[hull_vertices], hull_points, atol=1e-6):
            logging.error(
                "Hull points do not correspond to the correct indices in the original points array."
            )
            return False

        # Check that we have at least 3 points for a valid hull in 2D
        if len(hull_vertices) < 3:
            logging.error("Convex hull must have at least 3 vertices in 2D.")
            return False

        # Check convexity by ensuring all internal angles are less than 180 degrees
        n = len(hull_vertices)
        for i in range(n):
            prev_point = hull_points[i - 1]
            curr_point = hull_points[i]
            next_point = hull_points[(i + 1) % n]

            # Calculate vectors
            v1 = np.array([curr_point[0] - prev_point[0], curr_point[1] - prev_point[1]])
            v2 = np.array([next_point[0] - curr_point[0], next_point[1] - curr_point[1]])

            # Cross product should be positive for counter-clockwise ordering
            cross_product = v1[0] * v2[1] - v1[1] * v2[0]
            if cross_product < 0:
                logging.error("Hull is not convex or not ordered counter-clockwise.")
                return False

        # Check that all points are contained within or on the boundary of the hull
        for point in points:
            if self._point_outside_hull(point, hull_points):
                logging.error("Not all points are contained within the convex hull.")
                return False

        return True

    def _point_outside_hull(self, point: np.ndarray, hull_points: np.ndarray) -> bool:
        """
        Check if a point is outside the convex hull.

        :param point: A point (x, y).
        :param hull_points: List of (x, y) coordinates of the hull vertices in counter-clockwise order.
        :return: True if the point is outside the hull, False otherwise.
        """
        n = len(hull_points)
        for i in range(n):
            p1 = hull_points[i]
            p2 = hull_points[(i + 1) % n]

            # Check if the point is to the right of the edge (p1, p2)
            cross_product = (p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (
                point[0] - p1[0]
            )

            # If cross product is negative, the point is to the right of the edge (outside the hull)
            if cross_product < -1e-9:  # Using a small epsilon for numerical stability
                return True

        return False