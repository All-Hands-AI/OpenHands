# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random

from ortools.sat.python import cp_model



class Task:
    def __init__(self, **kwargs):
        """
        Initialize the MaxWeightedIndependentSet Task.

        Finds the maximum weighted independent set given the adjacency matrix and weights of a graph.
        Uses OR-Tools CP-SAT solver for an exact optimization formulation.
        """
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, list]:
        """
        Generates a random graph represented by an n×n adjacency matrix and random integer weights in [0, n].

        :param n: The number of nodes.
        :param random_seed: Seed for reproducibility.
        :return: A dict with keys:
                 - 'adj_matrix': n×n list of lists with 0/1 entries indicating edges.
                 - 'weights': list of length n, weights[i] ∈ [0, n].
        """
        random.seed(random_seed)
        prob = 0.15
        adj_matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if random.random() < prob:
                    adj_matrix[i][j] = 1
                    adj_matrix[j][i] = 1
        weights = [random.randint(0, n) for _ in range(n)]
        return {"adj_matrix": adj_matrix, "weights": weights}

    def solve(self, problem: dict[str, list]) -> list[int]:
        """
        Solves the MWIS problem using CP-SAT.

        :param problem: dict with 'adj_matrix' and 'weights'
        :return: list of selected node indices.
        """
        adj_matrix = problem["adj_matrix"]
        weights = problem["weights"]
        n = len(adj_matrix)
        model = cp_model.CpModel()
        nodes = [model.NewBoolVar(f"x_{i}") for i in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                if adj_matrix[i][j]:
                    model.Add(nodes[i] + nodes[j] <= 1)

        model.Maximize(sum(weights[i] * nodes[i] for i in range(n)))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        if status == cp_model.OPTIMAL:
            return [i for i in range(n) if solver.Value(nodes[i])]
        else:
            logging.error("No solution found.")
            return []

    def is_solution(self, problem: dict[str, list], solution: list[int]) -> bool:
        """
        Verifies independence and weight-optimality.

        :param problem: dict with 'adj_matrix' and 'weights'
        :param solution: candidate node indices
        :return: True if valid and optimal.
        """
        try:
            adj_matrix = problem["adj_matrix"]
            weights = problem["weights"]
            for a in range(len(solution)):
                for b in range(a + 1, len(solution)):
                    if adj_matrix[solution[a]][solution[b]]:
                        return False
            cand_val = sum(weights[i] for i in solution)
            opt = self.solve(problem)
            opt_val = sum(weights[i] for i in opt)
            return cand_val == opt_val
        except Exception as e:
            logging.error(f"Error verifying solution: {e}")
            return False