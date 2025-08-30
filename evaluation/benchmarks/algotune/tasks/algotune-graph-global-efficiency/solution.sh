#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numba
import numpy as np

# This function is JIT-compiled with Numba for performance.
# It avoids memory allocation within the main loop for maximum speed.
@numba.njit(cache=True, fastmath=True)
def _calculate_total_inverse_distance_optimized(n: int, offsets: np.ndarray, flat_adj: np.ndarray) -> float:
    """
    Calculates the sum of the inverse of all-pairs shortest path lengths.
    This optimized version pre-allocates memory for the BFS queue and distances array,
    and uses the highly optimized `fill` method to reset the distances array between
    BFS runs. This avoids the overhead of memory allocation within the main loop.
    """
    total_inverse_distance = 0.0

    # --- Pre-allocate memory outside the hot loop ---
    # This is a key optimization to avoid repeated allocation/deallocation overhead.
    distances = np.empty(n, dtype=np.int32)
    queue = np.empty(n, dtype=np.int32)

    # A serial loop over all possible starting nodes.
    for i in range(n):
        # --- Efficient Reset using `fill` ---
        # `fill` is a highly optimized method for setting all elements of an array.
        # This is faster than re-allocating a new array with `np.full` in every iteration.
        distances.fill(-1)
        
        # Start BFS from the current node `i`.
        head = 0
        tail = 0

        distances[i] = 0
        queue[tail] = i
        tail += 1
        
        while head < tail:
            u = queue[head]
            head += 1

            # Iterate through neighbors of u using the efficient flattened adjacency list.
            start = offsets[u]
            end = offsets[u+1]
            for j in range(start, end):
                v = flat_adj[j]
                if distances[v] == -1:
                    dist = distances[u] + 1
                    distances[v] = dist
                    total_inverse_distance += 1.0 / dist
                    queue[tail] = v
                    tail += 1
            
    return total_inverse_distance

class Solver:
    def solve(self, problem: dict, **kwargs) -> Any:
        """
        Calculates the global efficiency of the graph using a highly optimized,
        serial Numba kernel that avoids memory allocation in its main loop.
        """
        adj_list = problem["adjacency_list"]
        n = len(adj_list)

        if n <= 1:
            return {"global_efficiency": 0.0}

        # Convert the Python list of lists to a flattened adjacency list representation.
        # This is a highly efficient format for Numba.
        offsets = np.zeros(n + 1, dtype=np.int32)
        num_edges = sum(len(neighbors) for neighbors in adj_list)
        flat_adj = np.empty(num_edges, dtype=np.int32)
        
        current_pos = 0
        for i, neighbors in enumerate(adj_list):
            offsets[i] = current_pos
            num_neighbors = len(neighbors)
            if num_neighbors > 0:
                flat_adj[current_pos:current_pos + num_neighbors] = neighbors
            current_pos += num_neighbors
        offsets[n] = current_pos

        # Call the high-performance Numba function to do the heavy lifting.
        total_inverse_distance = _calculate_total_inverse_distance_optimized(n, offsets, flat_adj)
        
        denominator = n * (n - 1)
        
        global_efficiency = total_inverse_distance / denominator
        
        return {"global_efficiency": global_efficiency}
EOF
