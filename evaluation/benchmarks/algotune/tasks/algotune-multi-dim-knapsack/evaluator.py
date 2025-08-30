# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import NamedTuple

from ortools.sat.python import cp_model



class MultiDimKnapsackInstance(NamedTuple):
    value: list[int]  # item values               (length n)
    demand: list[list[int]]  # demand[i][r] = demand of item i in resource r (n × k)
    supply: list[int]  # resource capacities       (length k)


MultiKnapsackSolution = list[int]


class Task:
    """
    Multi-dimensional 0-1 knapsack solved with OR-Tools CP-SAT.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int = 1) -> MultiDimKnapsackInstance:
        logging.debug("Generating multi-dim knapsack: n=%d seed=%d", n, random_seed)
        rng = random.Random(random_seed + n)
        n = max(5, n)

        # Number of resource dimensions
        k = rng.randint(5, max(10, n // 50))

        # Capacities
        supply = [rng.randint(5 * n, 10 * n) for _ in range(k)]

        # Demands
        demand: list[list[int]] = [[0] * k for _ in range(n)]
        for j in range(k):
            factor = rng.uniform(0.1, 0.6)
            for i in range(n):
                mu = supply[j] / (factor * n)
                sigma = supply[j] / (factor * 1.5 * n)
                demand[i][j] = max(0, min(int(rng.gauss(mu, sigma)), supply[j]))

        # Item values
        value = [max(1, int(rng.gauss(50, 30))) for _ in range(n)]

        # Optional correlation between items
        for i in range(n):
            for j in range(k):
                if rng.random() < 0.3:
                    corr_item = rng.randint(0, n - 1)
                    offset = int(rng.uniform(-0.1, 0.1) * demand[corr_item][j])
                    demand[i][j] = max(0, min(demand[i][j] + offset, supply[j]))

        return MultiDimKnapsackInstance(value, demand, supply)

    def solve(
        self,
        problem: MultiDimKnapsackInstance | list | tuple,  # ← added annotation
    ) -> MultiKnapsackSolution:
        """
        Returns list of selected item indices. Empty list on failure.
        """
        if not isinstance(problem, MultiDimKnapsackInstance):
            try:
                problem = MultiDimKnapsackInstance(*problem)
            except Exception as e:
                logging.error("solve(): cannot parse problem – %s", e)
                return []

        n: int = len(problem.value)
        k: int = len(problem.supply)

        model = cp_model.CpModel()
        x = [model.NewBoolVar(f"x_{i}") for i in range(n)]

        for r in range(k):
            model.Add(sum(x[i] * problem.demand[i][r] for i in range(n)) <= problem.supply[r])
        model.Maximize(sum(x[i] * problem.value[i] for i in range(n)))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return [i for i in range(n) if solver.Value(x[i])]
        return []

    def is_solution(
        self,
        problem: MultiDimKnapsackInstance | list | tuple,
        solution: MultiKnapsackSolution,
    ) -> bool:
        if not isinstance(problem, MultiDimKnapsackInstance):
            try:
                problem = MultiDimKnapsackInstance(*problem)
            except Exception:
                logging.error("is_solution(): problem has wrong structure.")
                return False

        n = len(problem.value)
        k = len(problem.supply)

        # 1) index validity
        if not all(isinstance(i, int) and 0 <= i < n for i in solution):
            return False

        # 2) capacity feasibility
        for r in range(k):
            usage = sum(problem.demand[i][r] for i in solution)
            if usage > problem.supply[r]:
                return False

        # 3) optimality (compare to internal solver)
        sol_value = sum(problem.value[i] for i in solution)
        opt_value = sum(problem.value[i] for i in self.solve(problem))

        return sol_value >= opt_value