# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import networkx as nx
import numpy as np



class Task:
    """
    Find all articulation points in an undirected graph using networkx.articulation_points.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random undirected graph with n nodes, edges added with some probability.
        :param n: number of nodes
        :param random_seed: seed for reproducibility
        :return: dict with "num_nodes" and "edges"
        """
        random.seed(random_seed)
        np.random.seed(random_seed)

        num_nodes = max(2, n)
        p = 0.3
        edges = []
        for u in range(num_nodes):
            for v in range(u + 1, num_nodes):
                if np.random.rand() < p:
                    edges.append([u, v])

        # Ensure at least one edge if possible
        if len(edges) == 0 and num_nodes > 1:
            edges.append([0, 1])

        return {"num_nodes": num_nodes, "edges": edges}

    def solve(self, problem: dict[str, Any]) -> dict[str, list[int]]:
        """
        Build the undirected graph and find articulation points via networkx.
        Return them as a sorted list.
        """
        G = nx.Graph()
        G.add_nodes_from(range(problem["num_nodes"]))
        for u, v in problem["edges"]:
            G.add_edge(u, v)

        # articulation_points returns a generator
        ap_list = list(nx.articulation_points(G))
        ap_list.sort()
        return {"articulation_points": ap_list}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Validate by re-running articulation points and comparing the sorted lists.
        """
        if "articulation_points" not in solution:
            logging.error("Solution must contain 'articulation_points'.")
            return False

        ref = self.solve(problem)["articulation_points"]
        prop = solution["articulation_points"]
        if ref != prop:
            logging.error(
                f"Proposed articulation points differ from reference.\nRef: {ref}\nProp: {prop}"
            )
            return False

        return True