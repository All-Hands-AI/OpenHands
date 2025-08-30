# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
import random
from typing import Any

from ortools.sat.python import cp_model



class Task:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # --------------------------------------------------------------------- #
    # Problem generator                                                      #
    # --------------------------------------------------------------------- #
    def generate_problem(self, n: int, random_seed: int = 1) -> dict[str, Any]:
        """
        Generate a random DAP instance with n products and 2·n periods.

        Parameters
        ----------
        n : int
            Number of products (must be ≥ 1).
        random_seed : int, optional
            Seed for reproducibility.

        Returns
        -------
        Dict[str, Any]
            Keys:
                - "T"          : int, number of periods  (= 2 n)
                - "N"          : int, number of products (= n)
                - "prices"     : List[int] length N, price ≥ 1
                - "capacities" : List[int] length N, inventory ≥ 1
                - "probs"      : List[List[float]] shape (T×N), each in [0,1]
        """
        if n < 1:
            raise ValueError("Need n ≥ 1 to generate a DAP instance")

        random.seed(random_seed)
        T = 2 * n
        N = n

        prices = [random.randint(5, 100) for _ in range(N)]
        # total capacity roughly half the horizon so decisions matter
        capacities = [random.randint(1, max(1, T // 2)) for _ in range(N)]

        # draw purchase‑probabilities; larger for higher priced items less likely
        probs: list[list[float]] = []
        for t in range(T):
            row = [round(random.uniform(0.05, 0.9) * (50 / p), 3) for p in prices]
            # clip to [0,1]
            row = [min(1.0, max(0.0, v)) for v in row]
            probs.append(row)

        return {
            "T": T,
            "N": N,
            "prices": prices,
            "capacities": capacities,
            "probs": probs,
        }

    # --------------------------------------------------------------------- #
    # Solver                                                                 #
    # --------------------------------------------------------------------- #
    def solve(self, problem: dict[str, Any]) -> list[int]:
        """
        Solve the DAP exactly with a binary integer program (CP‑SAT).

        Returns
        -------
        List[int]
            offer[t] ∈ {‑1,0,…,N−1}.  ‑1 ⇒ offer nothing in period *t*.
        """
        T = problem["T"]
        N = problem["N"]
        prices = problem["prices"]
        capacities = problem["capacities"]
        probs = problem["probs"]

        model = cp_model.CpModel()

        # Decision vars: x[t,i] = 1 ⇔ offer product i in period t
        x = {(t, i): model.NewBoolVar(f"x_{t}_{i}") for t in range(T) for i in range(N)}

        # Each period at most one product
        for t in range(T):
            model.Add(sum(x[(t, i)] for i in range(N)) <= 1)

        # Capacity limits
        for i in range(N):
            model.Add(sum(x[(t, i)] for t in range(T)) <= capacities[i])

        # Objective: expected revenue
        model.Maximize(sum(prices[i] * probs[t][i] * x[(t, i)] for t in range(T) for i in range(N)))

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logging.error("No feasible solution found.")
            return [-1] * T

        offer = []
        for t in range(T):
            chosen = -1
            for i in range(N):
                if solver.Value(x[(t, i)]) == 1:
                    chosen = i
                    break
            offer.append(chosen)
        return offer

    # --------------------------------------------------------------------- #
    # Verifier                                                               #
    # --------------------------------------------------------------------- #
    def is_solution(self, problem: dict[str, Any], solution: list[int]) -> bool:
        """
        Check validity **and** optimality of a proposed policy.

        Validity:
          1. Length = T.
          2. Each entry ∈ {‑1,0,…,N−1}.
          3. For every product i, it is offered ≤ capacities[i] times.

        Optimality:
          4. Expected revenue equals our solver’s optimum (within 1e‑6).

        Returns
        -------
        bool
        """
        T = problem["T"]
        N = problem["N"]
        prices = problem["prices"]
        capacities = problem["capacities"]
        probs = problem["probs"]

        if len(solution) != T:
            return False

        counts = [0] * N
        exp_rev = 0.0
        for t, choice in enumerate(solution):
            if choice == -1:
                continue
            if not (0 <= choice < N):
                return False
            counts[choice] += 1
            if counts[choice] > capacities[choice]:
                return False
            exp_rev += prices[choice] * probs[t][choice]

        # Compare to optimal objective
        opt_solution = self.solve(problem)
        opt_rev = 0.0
        for t, choice in enumerate(opt_solution):
            if choice != -1:
                opt_rev += prices[choice] * probs[t][choice]

        return abs(exp_rev - opt_rev) < 1e-6


# ---------------------------------------------------------------------- #
# Example usage                                                          #
# ---------------------------------------------------------------------- #