#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
from ortools.graph.python import min_cost_flow

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> list[list[Any]]:
        """Solve maximum flow min cost using ortools."""
        capacity = problem["capacity"]
        cost = problem["cost"]
        s = problem["s"]
        t = problem["t"]
        n = len(capacity)
        
        # Create the min cost flow object
        mcf = min_cost_flow.SimpleMinCostFlow()
        
        # Add edges with capacity and cost
        for i in range(n):
            for j in range(n):
                if capacity[i][j] > 0:
                    mcf.add_arc_with_capacity_and_unit_cost(
                        i, j, capacity[i][j], cost[i][j]
                    )
        
        # Add supply and demand
        # We need to find max flow, so we set a large supply at source
        # and corresponding demand at sink
        max_possible_flow = sum(capacity[s][j] for j in range(n))
        mcf.set_node_supply(s, max_possible_flow)
        mcf.set_node_supply(t, -max_possible_flow)
        
        # Solve the problem
        status = mcf.solve()
        
        # Build solution matrix
        solution = [[0 for _ in range(n)] for _ in range(n)]
        
        if status == mcf.OPTIMAL:
            for arc in range(mcf.num_arcs()):
                i = mcf.tail(arc)
                j = mcf.head(arc)
                flow = mcf.flow(arc)
                if flow > 0:
                    solution[i][j] = flow
        
        return solution
EOF
