#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import cvxpy as cp
import numpy as np

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> dict[str, Any]:
        """
        Solve the aircraft wing design optimization problem using CVXPY.
        This implementation uses vectorization to speed up problem construction.
        """
        # Extract problem parameters
        num_conditions = problem["num_conditions"]
        conditions = problem["conditions"]

        # --- Vectorized Parameter Extraction ---
        CDA0 = np.array([c["CDA0"] for c in conditions])
        C_Lmax = np.array([c["C_Lmax"] for c in conditions])
        N_ult = np.array([c["N_ult"] for c in conditions])
        S_wetratio = np.array([c["S_wetratio"] for c in conditions])
        V_min = np.array([c["V_min"] for c in conditions])
        W_0 = np.array([c["W_0"] for c in conditions])
        W_W_coeff1 = np.array([c["W_W_coeff1"] for c in conditions])
        W_W_coeff2 = np.array([c["W_W_coeff2"] for c in conditions])
        e = np.array([c["e"] for c in conditions])
        k = np.array([c["k"] for c in conditions])
        mu = np.array([c["mu"] for c in conditions])
        rho = np.array([c["rho"] for c in conditions])
        tau = np.array([c["tau"] for c in conditions])

        # --- Define shared design variables ---
        A = cp.Variable(pos=True, name="A")  # aspect ratio
        S = cp.Variable(pos=True, name="S")  # wing area (m²)

        # --- Define condition-specific vectorized variables ---
        V = cp.Variable(num_conditions, pos=True, name="V")
        W = cp.Variable(num_conditions, pos=True, name="W")
        Re = cp.Variable(num_conditions, pos=True, name="Re")
        C_D = cp.Variable(num_conditions, pos=True, name="C_D")
        C_L = cp.Variable(num_conditions, pos=True, name="C_L")
        C_f = cp.Variable(num_conditions, pos=True, name="C_f")
        W_w = cp.Variable(num_conditions, pos=True, name="W_w")

        # --- Define constraints in vectorized form ---
        constraints = []

        # Drag coefficient model: C_D >= CDA0/S + k*C_f*S_wetratio + C_L^2/(pi*A*e)
        term1_cd = CDA0 * cp.inv_pos(S)
        term2_cd = cp.multiply(k * S_wetratio, C_f)
        term3_cd = cp.multiply(1 / (np.pi * e), cp.power(C_L, 2)) * cp.inv_pos(A)
        constraints.append(C_D >= term1_cd + term2_cd + term3_cd)

        # Skin friction model: C_f >= 0.074 / Re^0.2
        constraints.append(C_f >= 0.074 * cp.power(Re, -0.2))

        # Reynolds number definition: Re * mu >= rho * V * sqrt(S/A)
        constraints.append(
            cp.multiply(Re, mu) >= cp.multiply(rho, V) * cp.sqrt(S * cp.inv_pos(A))
        )

        # Wing weight model: W_w >= W_W_coeff2*S + W_W_coeff1*N_ult*A^(1.5)*sqrt(W_0*W)/tau
        term1_ww = W_W_coeff2 * S
        c_ww = (W_W_coeff1 * N_ult) / tau
        term2_ww = cp.multiply(c_ww * cp.power(A, 1.5), cp.sqrt(cp.multiply(W_0, W)))
        constraints.append(W_w >= term1_ww + term2_ww)

        # Total weight: W >= W_0 + W_w
        constraints.append(W >= W_0 + W_w)

        # Lift equals weight: W <= 0.5 * rho * V^2 * C_L * S
        constraints.append(
            W <= 0.5 * S * cp.multiply(rho, cp.multiply(cp.power(V, 2), C_L))
        )

        # Stall constraint: 2*W/(rho * V_min^2 * S) <= C_Lmax
        c_stall = 2 / (rho * V_min**2)
        constraints.append(cp.multiply(c_stall, W) * cp.inv_pos(S) <= C_Lmax)

        # --- Define the objective ---
        # Minimize average drag: (1/n) * sum(0.5 * rho * V^2 * C_D * S)
        drag_vec = 0.5 * S * cp.multiply(rho, cp.multiply(cp.power(V, 2), C_D))
        objective = cp.Minimize(cp.sum(drag_vec) / num_conditions)

        # --- Solve the problem ---
        prob = cp.Problem(objective, constraints)
        try:
            prob.solve(gp=True, solver=cp.ECOS, warm_start=True, feastol=1e-5, abstol=1e-4, reltol=1e-4)

            if prob.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE} or A.value is None:
                return {"A": [], "S": [], "avg_drag": 0.0, "condition_results": []}

            # --- Collect results ---
            condition_results = []
            drag_values = 0.5 * S.value * rho * (V.value**2) * C_D.value
            for i in range(num_conditions):
                condition_results.append(
                    {
                        "condition_id": conditions[i]["condition_id"],
                        "V": float(V.value[i]),
                        "W": float(W.value[i]),
                        "W_w": float(W_w.value[i]),
                        "C_L": float(C_L.value[i]),
                        "C_D": float(C_D.value[i]),
                        "C_f": float(C_f.value[i]),
                        "Re": float(Re.value[i]),
                        "drag": float(drag_values[i]),
                    }
                )

            return {
                "A": float(A.value),
                "S": float(S.value),
                "avg_drag": float(prob.value),
                "condition_results": condition_results,
            }

        except (cp.SolverError, Exception):
            return {"A": [], "S": [], "avg_drag": 0.0, "condition_results": []}
EOF
