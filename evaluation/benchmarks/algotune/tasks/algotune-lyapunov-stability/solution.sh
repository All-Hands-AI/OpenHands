#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any
import numpy as np
from scipy.linalg import solve_discrete_lyapunov
import numba as nb

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Optimized Lyapunov stability analysis with adaptive stability check."""
        A = np.array(problem["A"])
        n = A.shape[0]
        
        # Fast spectral radius estimation
        rho = self._spectral_radius(A, max_iters=20)
        if rho >= 1.0 - 1e-12:
            # Confirm with full eigenvalue decomposition if near boundary
            if rho >= 1.0 - 1e-8 or not self._is_stable(A):
                return {"is_stable": False, "P": None}
        
        try:
            # Solve Lyapunov equation with faster algorithm
            P = solve_discrete_lyapunov(A, np.eye(n))
            
            # Ensure symmetry and positive definiteness
            P_sym = (P + P.T) / 2
            P_sym += 1e-12 * np.eye(n)
            
            # Efficient verification
            if self._verify_solution(A, P_sym):
                return {"is_stable": True, "P": P_sym.tolist()}
        except Exception:
            pass
        
        # Fallback to SDP for problematic cases
        return self._solve_sdp(A)
    
    @staticmethod
    @nb.njit(cache=True, fastmath=True)
    def _spectral_radius(A, max_iters=20):
        """Power iteration for spectral radius estimation."""
        n = A.shape[0]
        v = np.random.rand(n)
        v /= np.linalg.norm(v)
        
        for _ in range(max_iters):
            Av = A @ v
            v_new = Av / np.linalg.norm(Av)
            v = v_new
            
        # Rayleigh quotient
        return np.abs(v @ A @ v)
    
    def _is_stable(self, A):
        """Full eigenvalue stability check."""
        eigvals = np.linalg.eigvals(A)
        return np.max(np.abs(eigvals)) < 1.0 - 1e-12
    
    @staticmethod
    @nb.njit(cache=True, fastmath=True)
    def _verify_solution(A, P):
        """Efficient solution verification with Cholesky."""
        try:
            L = np.linalg.cholesky(P)
        except:
            return False
        
        S = A.T @ P @ A - P
        try:
            np.linalg.cholesky(-S)
            return True
        except:
            return False
    
    def _solve_sdp(self, A):
        """Optimized SDP fallback with faster solver parameters."""
        import cvxpy as cp
        
        n = A.shape[0]
        P = cp.Variable((n, n), symmetric=True)
        constraints = [P >> np.eye(n), A.T @ P @ A - P << -np.eye(n)]
        prob = cp.Problem(cp.Minimize(0), constraints)
        prob.solve(solver=cp.SCS, eps=1e-4, max_iters=5000, use_indirect=True)
        
        if prob.status in ["optimal", "optimal_inaccurate"]:
            P_val = np.array(P.value)
            P_sym = (P_val + P_val.T) / 2
            return {"is_stable": True, "P": P_sym.tolist()}
        return {"is_stable": False, "P": None}
EOF
