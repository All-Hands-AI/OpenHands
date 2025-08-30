# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np
from scipy import signal



class Task:
    """
    Designs an FIR filter via least-squares (`scipy.signal.firls`).

        • Problem instance  →  (n, edges)
            n      – desired half-order (actual length = 2·n+1)
            edges  – two transition-band edge frequencies (0 < e₁ < e₂ < 1)

        • Solution          →  1-D NumPy array of length 2·n+1
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_edges: tuple[float, float] = (0.1, 0.9)

    def generate_problem(self, n: int, random_seed: int = 1) -> tuple[int, tuple[float, float]]:
        rng = np.random.default_rng(random_seed)
        offset = rng.uniform(-0.05, 0.05, size=2)
        edges = (self.base_edges[0] + offset[0], self.base_edges[1] + offset[1])
        return n, edges  # tuples survive JSON as lists; we’ll convert back later

    def solve(self, problem: tuple[int, tuple[float, float]]) -> np.ndarray:
        n, edges = problem
        n = 2 * n + 1  # actual filter length (must be odd)

        # JSON round-trip may turn `edges` into a list – convert to tuple
        edges = tuple(edges)

        coeffs = signal.firls(n, (0.0, *edges, 1.0), [1, 1, 0, 0])
        return coeffs

    def is_solution(self, problem: tuple[int, tuple[float, float]], solution: np.ndarray) -> bool:
        n, edges = problem
        n = 2 * n + 1
        edges = tuple(edges)

        try:
            reference = signal.firls(n, (0.0, *edges, 1.0), [1, 1, 0, 0])
        except Exception as e:
            logging.error(f"Reference firls failed: {e}")
            return False

        if solution.shape != reference.shape:
            logging.error(
                f"Shape mismatch: solution {solution.shape} vs reference {reference.shape}"
            )
            return False

        rel_err = np.linalg.norm(solution - reference) / (np.linalg.norm(reference) + 1e-12)
        return bool(rel_err <= 1e-6)