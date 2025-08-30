#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from ortools.algorithms.python import knapsack_solver

class Solver:
    def solve(self, problem, **kwargs) -> list:
        try:
            if isinstance(problem, tuple) and len(problem) == 3:
                value, demand, supply = problem
            else:
                value = problem.value
                demand = problem.demand
                supply = problem.supply
        except Exception:
            return []
        
        n = len(value)
        if n == 0:
            return []
        
        # Create solver
        solver = knapsack_solver.KnapsackSolver(
            knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
            ''
        )
        
        # Optimized weights matrix creation without unnecessary list conversion
        weights = list(zip(*demand))
        
        solver.init(value, weights, supply)
        solver.solve()
        
        return [i for i in range(n) if solver.best_solution_contains(i)]
EOF
