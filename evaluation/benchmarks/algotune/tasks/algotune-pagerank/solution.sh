#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
import numba
from typing import Any, List
import itertools

# This helper function is JIT-compiled by Numba for performance.
# It implements the core PageRank power iteration logic.
@numba.njit(cache=True, fastmath=True)
def _pagerank_numba(
    adj_list_indices: np.ndarray,
    adj_list_indptr: np.ndarray,
    out_degree: np.ndarray,
    n: int,
    alpha: float,
    max_iter: int,
    tol: float,
) -> np.ndarray:
    """
    Calculates PageRank scores using power iteration, accelerated with Numba.

    Args:
        adj_list_indices: CSR-style array of neighbor indices.
        adj_list_indptr: CSR-style array of index pointers.
        out_degree: Array of out-degrees for each node.
        n: Number of nodes in the graph.
        alpha: Damping factor.
        max_iter: Maximum number of iterations.
        tol: Convergence tolerance for L1 norm.

    Returns:
        A numpy array of PageRank scores.
    """
    # Initialize PageRank scores uniformly
    r = np.full(n, 1.0 / n, dtype=np.float64)

    # Identify dangling nodes (nodes with no outgoing links)
    dangling_nodes_mask = out_degree == 0
    
    # Pre-calculate the constant teleportation term
    teleport_val = (1.0 - alpha) / n

    for _ in range(max_iter):
        r_last = r
        r_new = np.zeros(n, dtype=np.float64)

        # 1. Calculate the total rank from dangling nodes
        dangling_rank_sum = 0.0
        # This loop is faster inside numba than np.sum(r_last[dangling_nodes_mask])
        for i in range(n):
            if dangling_nodes_mask[i]:
                dangling_rank_sum += r_last[i]
        
        # Distribute dangling rank and teleportation probability to all nodes
        dangling_and_teleport = alpha * (dangling_rank_sum / n) + teleport_val
        r_new += dangling_and_teleport

        # 2. Distribute rank from non-dangling nodes
        for i in range(n):
            if not dangling_nodes_mask[i]:
                # Distribute this node's rank to its neighbors
                start = adj_list_indptr[i]
                end = adj_list_indptr[i + 1]
                rank_to_distribute = alpha * r_last[i] / out_degree[i]
                for k in range(start, end):
                    j = adj_list_indices[k]
                    r_new[j] += rank_to_distribute
        
        r = r_new

        # 3. Check for convergence using L1 norm
        err = 0.0
        for i in range(n):
            err += abs(r[i] - r_last[i])
        
        if err < n * tol: # Scale tolerance by n as in networkx
            break
            
    return r

class Solver:
    """
    A solver for the PageRank problem that uses a Numba-accelerated
    power iteration method for high performance.
    """
    def __init__(self):
        """Initializes the solver with default PageRank parameters."""
        self.alpha = 0.85
        self.max_iter = 100
        self.tol = 1.0e-6 # networkx default tolerance

    def solve(self, problem: dict[str, List[List[int]]], **kwargs) -> dict[str, Any]:
        """
        Calculates PageRank scores for a given graph.

        Args:
            problem: A dictionary containing the adjacency list of the graph.
            **kwargs: Can be used to override default parameters like alpha, max_iter, tol.

        Returns:
            A dictionary with the key "pagerank_scores" and a list of scores.
        """
        adj_list = problem["adjacency_list"]
        n = len(adj_list)

        if n == 0:
            return {"pagerank_scores": []}
        if n == 1:
            return {"pagerank_scores": [1.0]}

        # Override parameters if provided in kwargs
        alpha = kwargs.get("alpha", self.alpha)
        max_iter = kwargs.get("max_iter", self.max_iter)
        tol = kwargs.get("tol", self.tol)

        # Optimized conversion of adjacency list to CSR-like format
        
        # Calculate out_degrees (lengths of neighbor lists)
        out_degree = np.array([len(neighbors) for neighbors in adj_list], dtype=np.int32)

        # Efficiently create indptr using cumsum
        indptr = np.empty(n + 1, dtype=np.int32)
        indptr[0] = 0
        np.cumsum(out_degree, out=indptr[1:])

        # Efficiently create indices by flattening the adjacency list
        num_edges = indptr[-1]
        indices = np.fromiter(itertools.chain.from_iterable(adj_list), 
                              dtype=np.int32, 
                              count=num_edges)

        # Call the Numba-jitted function to perform the calculation
        pagerank_scores_np = _pagerank_numba(
            indices, indptr, out_degree, n, alpha, max_iter, tol
        )

        return {"pagerank_scores": pagerank_scores_np.tolist()}
EOF
