# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging

import numpy as np



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1234) -> tuple[np.ndarray, np.ndarray]:
        np.random.seed(random_seed)
        vec1 = np.random.rand(n)
        vec2 = np.random.rand(n)
        return vec1, vec2

    def solve(self, problem: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        vec1, vec2 = problem
        outer_product = np.outer(vec1, vec2)
        return outer_product

    def is_solution(self, problem: tuple[np.ndarray, np.ndarray], solution: np.ndarray) -> bool:
        vec1, vec2 = problem
        reference = np.outer(vec1, vec2)
        tol = 1e-6
        error = (
            2
            * np.linalg.norm(solution - reference)
            / (np.linalg.norm(reference + solution) + 1e-12)
        )
        if error > tol:
            logging.error(f"Vector outer product error {error} exceeds tolerance {tol}.")
            return False
        return True