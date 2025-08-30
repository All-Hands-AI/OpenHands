#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
try:
    import numba
    from numba import njit
    NUMBA = True
except ImportError:
    NUMBA = False
if NUMBA:
    @njit(cache=True, fastmath=True)
    def _filter_smooth_numba(A, B, C, y, x0, tau):
        N = y.shape[0]
        m = y.shape[1]
        n = A.shape[1]
        p = B.shape[1]
        # Preallocate arrays
        x_pred = np.zeros((N+1, n))
        P_pred = np.zeros((N+1, n, n))
        x_filt = np.zeros((N+1, n))
        P_filt = np.zeros((N+1, n, n))
        # Covariances
        Q = B.dot(B.T)
        R = np.eye(m) / tau
        # Pseudo-inverse for B: M = (B^T B)^{-1} B^T
        BtB = B.T.dot(B)
        BtB_inv = np.linalg.inv(BtB)
        B_pinv = BtB_inv.dot(B.T)
        I_n = np.eye(n)
        # Initial state
        for i in range(n):
            x_pred[0, i] = x0[i]
        # Forward filter
        for t in range(N):
            Pt = P_pred[t]
            S = C.dot(Pt).dot(C.T) + R
            Sinv = np.linalg.inv(S)
            K = Pt.dot(C.T).dot(Sinv)
            innov = y[t] - C.dot(x_pred[t])
            x_filt[t] = x_pred[t] + K.dot(innov)
            P_filt[t] = (I_n - K.dot(C)).dot(Pt)
            x_pred[t+1] = A.dot(x_filt[t])
            P_pred[t+1] = A.dot(P_filt[t]).dot(A.T) + Q
        # Final update
        x_filt[N] = x_pred[N]
        P_filt[N] = P_pred[N]
        # Backward smoother
        x_smooth = np.zeros((N+1, n))
        x_smooth[N] = x_filt[N]
        for t in range(N-1, -1, -1):
            Pnext_inv = np.linalg.inv(P_pred[t+1])
            J = P_filt[t].dot(A.T).dot(Pnext_inv)
            x_smooth[t] = x_filt[t] + J.dot(x_smooth[t+1] - x_pred[t+1])
        # Recover noise estimates
        w_hat = np.zeros((N, p))
        v_hat = np.zeros((N, m))
        for t in range(N):
            diff = x_smooth[t+1] - A.dot(x_smooth[t])
            w_hat[t] = B_pinv.dot(diff)
            v_hat[t] = y[t] - C.dot(x_smooth[t])
        return x_smooth, w_hat, v_hat

    # Warm-up Numba compile (should use invertible covariances)
    try:
        _filter_smooth_numba(
            np.eye(1, dtype=np.float64),
            np.eye(1, dtype=np.float64),
            np.eye(1, dtype=np.float64),
            np.zeros((1, 1), dtype=np.float64),
            np.zeros(1, dtype=np.float64),
            1.0
        )
    except:
        pass
class Solver:
    def solve(self, problem, **kwargs):
        # Parse inputs
        if isinstance(problem, str):
            import json
            problem = json.loads(problem)
        A = np.array(problem["A"], dtype=np.float64)
        B = np.array(problem["B"], dtype=np.float64)
        C = np.array(problem["C"], dtype=np.float64)
        y = np.array(problem["y"], dtype=np.float64)
        x0 = np.array(problem["x_initial"], dtype=np.float64)
        tau = float(problem["tau"])
        # Filter & smooth
        if NUMBA:
            # Numba-accelerated Kalman filter, RTS smoother, and noise recovery
            x_smooth, w_hat_arr, v_hat_arr = _filter_smooth_numba(A, B, C, y, x0, tau)
            return {
                "x_hat": x_smooth.tolist(),
                "w_hat": w_hat_arr.tolist(),
                "v_hat": v_hat_arr.tolist(),
            }
        else:
            # Pure NumPy fallback: Kalman filter + RTS smoother
            N, m = y.shape
            n = A.shape[1]
            Q = B @ B.T
            R = np.eye(m) / tau
            x_pred = np.zeros((N+1, n))
            P_pred = np.zeros((N+1, n, n))
            x_filt = np.zeros((N+1, n))
            P_filt = np.zeros((N+1, n, n))
            x_pred[0] = x0
            I_n = np.eye(n)
            for t in range(N):
                Pt = P_pred[t]
                S = C @ Pt @ C.T + R
                K = Pt @ C.T @ np.linalg.inv(S)
                x_filt[t] = x_pred[t] + K @ (y[t] - C @ x_pred[t])
                P_filt[t] = (I_n - K @ C) @ Pt
                x_pred[t+1] = A @ x_filt[t]
                P_pred[t+1] = A @ P_filt[t] @ A.T + Q
            x_filt[N] = x_pred[N]
            P_filt[N] = P_pred[N]
            x_smooth = np.zeros((N+1, n))
            x_smooth[N] = x_filt[N]
            for t in range(N-1, -1, -1):
                Pnext = P_pred[t+1]
                J = P_filt[t] @ A.T @ np.linalg.inv(Pnext)
                x_smooth[t] = x_filt[t] + J @ (x_smooth[t+1] - x_pred[t+1])
            # Recover noise estimates
            # Enforce initial state constraint
            x_smooth[0] = x0
            diffs = x_smooth[1:] - x_smooth[:-1].dot(A.T)
            B_pinv = np.linalg.pinv(B)
            w_hat_arr = diffs.dot(B_pinv.T)
            v_hat_arr = y - x_smooth[:-1].dot(C.T)
            return {
                "x_hat": x_smooth.tolist(),
                "w_hat": w_hat_arr.tolist(),
                "v_hat": v_hat_arr.tolist(),
            }
EOF
