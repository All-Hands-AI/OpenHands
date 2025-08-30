#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy import signal
import numba
from numba import jit, float64

@jit(nopython=True, fastmath=True)
def taylor_expm(M, max_terms=15):
    """Compute matrix exponential using Taylor series approximation."""
    n = M.shape[0]
    expM = np.eye(n)
    term = np.eye(n)
    for k in range(1, max_terms+1):
        term = term @ M / k
        expM += term
    return expM

class Solver:
    def __init__(self):
        self.cache = {}
    
    def solve(self, problem: dict) -> dict:
        num = problem["num"]
        den = problem["den"]
        u = problem["u"]
        t = problem["t"]
        
        # Convert to state-space
        A, B, C, D = signal.tf2ss(num, den)
        n = A.shape[0]
        
        # Handle static systems
        if n == 0:
            return {"yout": [float(D * val) for val in u]}
        
        # Precompute constant matrices
        B = B.flatten()
        C = C.flatten()
        D = D.item() if D.size == 1 else D
        
        # Initialize output array
        yout = np.zeros(len(t))
        yout[0] = D * u[0]
        
        # Compute time steps
        dts = np.diff(t)
        constant_dt = len(dts) > 0 and np.all(np.abs(dts - dts[0]) < 1e-10)
        
        # Precompute matrices
        if constant_dt:
            # Single dt for all steps
            dt = dts[0]
            if dt > 1e-8:
                cache_key = (dt, tuple(A.ravel()), tuple(B))
                if cache_key not in self.cache:
                    M = np.zeros((n+2, n+2))
                    M[:n, :n] = A * dt
                    M[:n, n] = B * dt
                    M[:n, n+1] = np.zeros(n)
                    M[n, n+1] = 1
                    expM = taylor_expm(M)
                    F = expM[:n, :n]
                    G1 = expM[:n, n]
                    G2 = expM[:n, n+1]
                    self.cache[cache_key] = (F, G1, G2)
                
                F_val, G1_val, G2_val = self.cache[cache_key]
                F_arr = np.tile(F_val, (len(dts), 1, 1))
                G1_arr = np.tile(G1_val, (len(dts), 1))
                G2_arr = np.tile(G2_val, (len(dts), 1))
            else:
                F_arr = np.tile(np.eye(n), (len(dts), 1, 1))
                G1_arr = np.zeros((len(dts), n))
                G2_arr = np.zeros((len(dts), n))
        else:
            # Variable time steps
            F_arr = np.zeros((len(dts), n, n))
            G1_arr = np.zeros((len(dts), n))
            G2_arr = np.zeros((len(dts), n))
            
            # Precompute for each dt value
            for i, dt in enumerate(dts):
                if dt > 1e-8:
                    cache_key = (dt, tuple(A.ravel()), tuple(B))
                    if cache_key not in self.cache:
                        M = np.zeros((n+2, n+2))
                        M[:n, :n] = A * dt
                        M[:n, n] = B * dt
                        M[:n, n+1] = np.zeros(n)
                        M[n, n+1] = 1
                        expM = taylor_expm(M)
                        F = expM[:n, :n]
                        G1 = expM[:n, n]
                        G2 = expM[:n, n+1]
                        self.cache[cache_key] = (F, G1, G2)
                    
                    F_arr[i], G1_arr[i], G2_arr[i] = self.cache[cache_key]
                else:
                    F_arr[i] = np.eye(n)
                    G1_arr[i] = np.zeros(n)
                    G2_arr[i] = np.zeros(n)
        
        # Run optimized simulation
        x = np.zeros(n)
        u_arr = np.asarray(u)
        yout = self.numba_simulate(F_arr, G1_arr, G2_arr, u_arr, C, D, n, yout, len(dts))
        
        return {"yout": yout.tolist()}
    
    @staticmethod
    @jit(nopython=True, fastmath=True, boundscheck=False)
    def numba_simulate(F_arr, G1_arr, G2_arr, u, C, D, n, yout, num_steps):
        x = np.zeros(n)
        D_val = D
        C_vec = C
        
        # Handle scalar systems
        if n == 1:
            for i in range(num_steps):
                F = F_arr[i,0,0]
                G1 = G1_arr[i,0]
                G2 = G2_arr[i,0]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F*x[0] + G1*u0 + G2*du
                x[0] = x0
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0
            return yout
        
        # Specialized loops for common system orders
        if n == 2:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + G1[1]*u0 + G2[1]*du
                x[0], x[1] = x0, x1
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1
        elif n == 3:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + F[0,2]*x[2] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + F[1,2]*x[2] + G1[1]*u0 + G2[1]*du
                x2 = F[2,0]*x[0] + F[2,1]*x[1] + F[2,2]*x[2] + G1[2]*u0 + G2[2]*du
                x[0], x[1], x[2] = x0, x1, x2
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1 + C_vec[2]*x2
        elif n == 4:
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                x0 = F[0,0]*x[0] + F[0,1]*x[1] + F[0,2]*x[2] + F[0,3]*x[3] + G1[0]*u0 + G2[0]*du
                x1 = F[1,0]*x[0] + F[1,1]*x[1] + F[1,2]*x[2] + F[1,3]*x[3] + G1[1]*u0 + G2[1]*du
                x2 = F[2,0]*x[0] + F[2,1]*x[1] + F[2,2]*x[2] + F[2,3]*x[3] + G1[2]*u0 + G2[2]*du
                x3 = F[3,0]*x[0] + F[3,1]*x[1] + F[3,2]*x[2] + F[3,3]*x[3] + G1[3]*u0 + G2[3]*du
                x[0], x[1], x[2], x[3] = x0, x1, x2, x3
                
                # Output calculation
                yout[i+1] = D_val * u1 + C_vec[0]*x0 + C_vec[1]*x1 + C_vec[2]*x2 + C_vec[3]*x3
        else:
            # General case for higher-order systems
            for i in range(num_steps):
                F = F_arr[i]
                G1 = G1_arr[i]
                G2 = G2_arr[i]
                u0 = u[i]
                u1 = u[i+1]
                du = u1 - u0
                
                # State update with slope term
                new_x = np.zeros(n)
                for j in range(n):
                    temp = 0.0
                    for k in range(n):
                        temp += F[j, k] * x[k]
                    new_x[j] = temp + G1[j]*u0 + G2[j]*du
                x = new_x
                
                # Output calculation
                output_val = D_val * u1
                for j in range(n):
                    output_val += C_vec[j] * x[j]
                yout[i+1] = output_val
        
        return yout
EOF
