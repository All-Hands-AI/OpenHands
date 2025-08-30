# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

import networkx as nx



SolutionType = dict[str, int]
INTRA_COMPONENT_EDGE_PROB = 0.2  # probability for edges *within* a component


class Task:
    """
    Generate a graph composed of several disconnected Erdős–Rényi sub‑graphs
    and ask for the number of connected components.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _generate_components(self, n: int, rng: random.Random) -> nx.Graph:
        if n <= 1:
            return nx.empty_graph(n)

        k = rng.randint(2, min(5, n))  # number of components
        cuts = sorted(rng.sample(range(1, n), k - 1))
        sizes = [b - a for a, b in zip([0] + cuts, cuts + [n])]

        G, base = nx.Graph(), 0
        for size in sizes:
            while True:
                H = nx.fast_gnp_random_graph(
                    size,
                    INTRA_COMPONENT_EDGE_PROB,
                    seed=rng.randint(0, 2**32 - 1),
                )
                if size == 1 or nx.is_connected(H):
                    break
            G.update(nx.relabel_nodes(H, {i: base + i for i in H.nodes()}))
            base += size
        return G

    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        rng = random.Random(random_seed)
        G = nx.empty_graph(n) if n <= 1 else self._generate_components(n, rng)

        # randomise node labels
        perm = list(G.nodes())
        rng.shuffle(perm)
        G = nx.relabel_nodes(G, dict(zip(G.nodes(), perm)))

        return {"edges": list(G.edges()), "num_nodes": n}

    def solve(self, problem: dict[str, Any]) -> SolutionType:
        try:
            n = problem.get("num_nodes", 0)
            G = nx.Graph()
            G.add_nodes_from(range(n))  # include isolated nodes
            G.add_edges_from(problem["edges"])
            cc = nx.number_connected_components(G)
            return {"number_connected_components": cc}
        except Exception as e:
            logging.error(f"Counting connected components failed: {e}")
            # Use -1 as an unmistakable “solver errored” sentinel
            return {"number_connected_components": -1}

    def is_solution(
        self,
        problem: dict[str, Any],
        solution: SolutionType,
    ) -> bool:
        if solution.get("number_connected_components", -1) == -1:
            logging.error("Solution contained sentinel -1 (solver failure).")
            return False

        expected = self.solve(problem)["number_connected_components"]
        return expected == solution["number_connected_components"]