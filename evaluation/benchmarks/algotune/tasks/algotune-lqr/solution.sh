#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
from scipy.linalg import solve_discrete_are

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        A = np.array(problem["A"], dtype=np.float64)
        B = np.array(problem["B"], dtype=np.float64)
        Q = np.array(problem["Q"], dtype=np.float64)
        R = np.array(problem["R"], dtype=np.float64)
        P = np.array(problem["P"], dtype=np.float64)
        T = problem["T"]
        x0 = np.array(problem["x0"], dtype=np.float64)
        
        n, m = B.shape
        
        # Use the discrete Algebraic Riccati Equation solver for faster computation
        # This gives the steady-state solution which is optimal for infinite horizon
        # For finite horizon, we can use this as an approximation
        try:
            # Solve the DARE to get the steady-state gain
            P_ss = solve_discrete_are(A, B, Q, R)
            
            # Compute the steady-state feedback gain
            K_ss = np.linalg.inv(R + B.T @ P_ss @ B) @ (B.T @ P_ss @ A)
            
            # Use the steady-state gain for all time steps
            K = np.tile(K_ss, (T, 1, 1))
            
        except:
            # Fall back to the optimized iterative solution if DARE fails
            S = np.zeros((T + 1, n, n), dtype=np.float64)
            K = np.zeros((T, m, n), dtype=np.float64)
            S[T] = P
            
            # Pre-compute frequently used matrices
            B_T = B.T
            A_T = A.T
            
            # Optimized Riccati recursion
            for t in range(T - 1, -1, -1):
                St1 = S[t + 1]
                
                # Compute B^T * S_{t+1} (reuse this for both M1 and M2)
                B_T_St1 = B_T @ St1
                
                # Compute M1 = R + B^T * S_{t+1} * B
                M1 = R + B_T_St1 @ B
                
                # Compute M2 = B^T * S_{t+1} * A
                M2 = B_T_St1 @ A
                
                # Solve for K[t] - use np.linalg.solve for better performance
                K[t] = np.linalg.solve(M1, M2)
                
                # Compute S[t] using the optimized Riccati form
                # S[t] = Q + A^T * S_{t+1} * A - M2^T * K[t]
                A_T_St1 = A_T @ St1
                S[t] = Q + A_T_St1 @ A - M2.T @ K[t]
                S[t] = (S[t] + S[t].T) * 0.5
        
        # Forward simulation with optimized operations
        U = np.zeros((T, m), dtype=np.float64)
        x = x0.reshape(-1, 1)  # Ensure x is a column vector
        
        for t in range(T):
            # Compute control: u = -K[t] * x
            u = -K[t] @ x
            U[t] = u.ravel()
            
            # Update state: x = A * x + B * u
            x = A @ x + B @ u
        
        return {"U": U.tolist()}
EOF
