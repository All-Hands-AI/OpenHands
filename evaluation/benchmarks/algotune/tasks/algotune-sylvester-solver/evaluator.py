# Copyright (c) 2025 Ori Press and the AlgoTune contributors
# https://github.com/oripress/AlgoTune
import logging
from typing import Any

import numpy as np
from scipy.linalg import solve_sylvester



ABS_TOL = 1e-9
REL_TOL = 1e-6
SPECTRUM_GAP_THRESHOLD = 1e-3  # Minimum gap between spectra of A and -B
MAX_GENERATION_ATTEMPTS = 100


class Task:
    """
    Benchmark solving the Sylvester equation A X + X B = Q using scipy.linalg.solve_sylvester.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_problem(self, n: int, random_seed: int) -> dict[str, Any]:
        """
        Generates complex matrices A, B and Q such that AX+XB=Q has a unique solution.
        Ensures that the spectra of A and -B do not overlap.
        """
        if n <= 0:
            raise ValueError("Matrix dimension n must be positive.")

        rng = np.random.default_rng(random_seed)

        # Generate complex matrices ensuring no spectrum overlap
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            # Generate complex matrices
            A = rng.normal(size=(n, n)) + rng.normal(size=(n, n)) * 1j
            B = rng.normal(size=(n, n)) + rng.normal(size=(n, n)) * 1j

            # Check spectrum overlap
            A_spec, _ = np.linalg.eig(A)
            negB_spec, _ = np.linalg.eig(-B)

            # Calculate minimum gap between spectra
            smallest_gap = np.min(np.abs(A_spec[:, np.newaxis] - negB_spec[np.newaxis, :]))

            if smallest_gap > SPECTRUM_GAP_THRESHOLD:
                break
        else:
            raise RuntimeError(
                f"Failed to generate matrices with non-overlapping spectra after {MAX_GENERATION_ATTEMPTS} attempts"
            )

        # Generate complex Q
        Q = rng.normal(size=(n, n)) + rng.normal(size=(n, n)) * 1j

        logging.debug(
            "Generated Sylvester problem (n=%d, seed=%d, spectrum gap=%.3e).",
            n,
            random_seed,
            smallest_gap,
        )
        return {"A": A, "B": B, "Q": Q}

    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        A, B, Q = problem["A"], problem["B"], problem["Q"]

        logging.debug("Solving Sylvester equation (n=%d).", A.shape[0])
        X = solve_sylvester(A, B, Q)

        logging.debug("Solved Sylvester equation successfully.")
        return {"X": X}

    def is_solution(self, problem: dict[str, Any], solution: dict[str, Any]) -> bool:
        X = solution.get("X")
        if X is None:
            logging.error("Missing solution X")
            return False

        A, B, Q = problem["A"], problem["B"], problem["Q"]
        n, m = Q.shape

        # shape check
        if X.shape != (n, m):
            logging.error("Shape mismatch: X.shape=%s, expected (%d, %d).", X.shape, n, m)
            return False

        # finiteness check
        if not np.isfinite(X).all():
            logging.error("Non-finite entries detected in X.")
            return False

        # residual check using np.allclose
        AX_plus_XB = A @ X + X @ B
        if not np.allclose(AX_plus_XB, Q, rtol=REL_TOL, atol=ABS_TOL):
            residual = AX_plus_XB - Q
            res_norm = np.linalg.norm(residual, ord="fro")
            q_norm = np.linalg.norm(Q, ord="fro")
            logging.error(
                "Residual too high: ‖AX+XB-Q‖=%.3e, ‖Q‖=%.3e.",
                res_norm,
                q_norm,
            )
            return False

        logging.debug("Solution verified.")
        return True