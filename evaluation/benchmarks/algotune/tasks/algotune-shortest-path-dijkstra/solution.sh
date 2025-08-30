#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
import scipy.sparse
import scipy.sparse.csgraph
from typing import Any
import dask

# Attempt to import graph-tool and set a flag. This makes the solver robust
# to different environments and allows for a high-performance path.
try:
    import graph_tool.topology
    import graph_tool.Graph
    GRAPH_TOOL_AVAILABLE = True
except ImportError:
    GRAPH_TOOL_AVAILABLE = False

# This dask-decorated function is part of the fallback solution.
@dask.delayed
def _apsp_on_component_fallback(subgraph, original_indices):
    """Dask-delayed function for the fallback solver."""
    sub_dist_matrix = scipy.sparse.csgraph.shortest_path(
        csgraph=subgraph, method='auto', directed=False
    )
    return sub_dist_matrix, original_indices

class Solver:
    def _solve_with_graph_tool(self, graph_csr: scipy.sparse.csr_matrix) -> np.ndarray:
        """High-performance solver using the graph-tool library."""
        n_nodes = graph_csr.shape[0]
        g = graph_tool.Graph(directed=False)
        g.add_vertex(n_nodes)
        weights = g.new_edge_property("double")
        
        graph_coo = scipy.sparse.triu(graph_csr).tocoo()
        edge_list_with_weights = np.column_stack((graph_coo.row, graph_coo.col, graph_coo.data))
        g.add_edge_list(edge_list_with_weights, eprops=[weights])
        
        dist_generator = graph_tool.topology.shortest_distance(g, weights=weights)
        dist_matrix = np.array([dist_map.a for dist_map in dist_generator])
        return dist_matrix

    def _solve_with_scipy(self, graph_csr: scipy.sparse.csr_matrix) -> np.ndarray:
        """Fallback solver using SciPy and Dask for component-based parallelism."""
        n_nodes = graph_csr.shape[0]
        n_components, labels = scipy.sparse.csgraph.connected_components(
            csgraph=graph_csr, directed=False, return_labels=True
        )

        if n_components == 1:
            dist_matrix = scipy.sparse.csgraph.shortest_path(
                csgraph=graph_csr, method='auto', directed=False
            )
        else:
            dist_matrix = np.full((n_nodes, n_nodes), np.inf)
            np.fill_diagonal(dist_matrix, 0)
            component_nodes_list = [np.where(labels == i)[0] for i in range(n_components)]
            tasks = []
            for nodes in component_nodes_list:
                if len(nodes) > 1:
                    subgraph = graph_csr[nodes, :][:, nodes]
                    tasks.append(_apsp_on_component_fallback(subgraph, nodes))
            if tasks:
                results = dask.compute(*tasks, scheduler='threads')
                for sub_dist_matrix, original_indices in results:
                    ix_ = np.ix_(original_indices, original_indices)
                    dist_matrix[ix_] = sub_dist_matrix
        return dist_matrix

    def solve(self, problem: dict[str, Any], **kwargs) -> Any:
        """
        Solves the All-Pairs Shortest Path problem by dispatching to the best
        available backend.
        """
        try:
            graph_csr = scipy.sparse.csr_matrix(
                (problem["data"], problem["indices"], problem["indptr"]), shape=problem["shape"]
            )
        except Exception:
            return {"distance_matrix": []}

        n_nodes = graph_csr.shape[0]
        if n_nodes == 0:
            return {"distance_matrix": []}

        if GRAPH_TOOL_AVAILABLE:
            dist_matrix = self._solve_with_graph_tool(graph_csr)
        else:
            dist_matrix = self._solve_with_scipy(graph_csr)

        dist_matrix_obj = dist_matrix.astype(object)
        dist_matrix_obj[np.isinf(dist_matrix)] = None
        return {"distance_matrix": dist_matrix_obj.tolist()}
EOF
