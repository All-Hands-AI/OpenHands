# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import networkx as nx
import numpy as np



class Task:
    """
    Given an undirected weighted graph, find its Minimum Spanning Tree (MST).
    Uses networkx's built-in MST algorithm for reference.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random undirected graph with n nodes and random weighted edges.
        We'll pick edges with probability p, and each edge has a random weight.

        :param n: Number of nodes
        :param random_seed: For reproducibility
        :return: dict with 'num_nodes' and 'edges'
        """
        random.seed(random_seed)
        np.random.seed(random_seed)

        num_nodes = max(2, n)  # at least 2
        p = 0.3  # edge probability
        edges = []
        for u in range(num_nodes):
            for v in range(u + 1, num_nodes):
                if np.random.rand() < p:
                    w = round(np.random.uniform(0.1, 10.0), 3)
                    edges.append([u, v, w])

        # Ensure connectivity if possible by forcing at least a spanning chain
        # if we have fewer than (num_nodes - 1) edges, let's add edges to connect them
        # in a simple chain
        if len(edges) < (num_nodes - 1):
            edges = []
            for u in range(num_nodes - 1):
                w = round(np.random.uniform(0.1, 10.0), 3)
                edges.append([u, u + 1, w])

        return {"num_nodes": num_nodes, "edges": edges}

    def solve(self, problem: dict[str, Any]) -> dict[str, list[list[float]]]:
        """
        Construct the graph in networkx, compute MST using minimum_spanning_edges,
        and return the MST edges sorted by (u, v).

        :param problem: dict with 'num_nodes', 'edges'
        :return: dict with 'mst_edges'
        """
        G = nx.Graph()
        num_nodes = problem["num_nodes"]
        edges = problem["edges"]

        G.add_nodes_from(range(num_nodes))
        for u, v, w in edges:
            G.add_edge(u, v, weight=w)

        # networkx returns an iterator of MST edges
        mst_edges_data = list(nx.minimum_spanning_edges(G, data=True))

        # Convert to [u, v, weight]
        # each edge is (u, v, {'weight': w})
        mst_edges = []
        for u, v, data in mst_edges_data:
            # ensure u < v for sorting consistency
            if u > v:
                u, v = v, u
            mst_edges.append([u, v, data["weight"]])

        # Sort by (u, v)
        mst_edges.sort(key=lambda x: (x[0], x[1]))
        return {"mst_edges": mst_edges}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        """
        Validate by recomputing the MST and comparing the edge sets exactly.

        :param problem: dict with 'num_nodes', 'edges'
        :param solution: dict with 'mst_edges'
        :return: bool
        """
        if "mst_edges" not in solution:
            logging.error("Solution must contain 'mst_edges'.")
            return False

        ref = self.solve(problem)["mst_edges"]
        proposed = solution["mst_edges"]

        if len(proposed) != len(ref):
            logging.error("Proposed MST has different number of edges than reference MST.")
            return False

        # Compare edge by edge
        if proposed != ref:
            logging.error(
                f"Proposed MST edges differ from reference MST edges.\nRef: {ref}\nProp: {proposed}"
            )
            return False

        return True