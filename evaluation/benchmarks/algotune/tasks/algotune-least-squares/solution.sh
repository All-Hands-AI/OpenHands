#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
from scipy.optimize import least_squares, leastsq
from typing import Any, Callable
import multiprocessing
import time

def _safe_exp(z: np.ndarray | float) -> np.ndarray | float:
    """Exponentiation clipped to avoid overflow."""
    return np.exp(np.clip(z, -50.0, 50.0))

def _run_optimization(residual, guess, bounds, timeout):
    """Run optimization with timeout using multiprocessing."""
    def worker(res, res_queue):
        try:
            result = least_squares(residual, guess, bounds=bounds, max_nfev=5000)
            res_queue.put(result)
        except Exception as e:
            res_queue.put(e)
    
    res_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(residual, res_queue))
    p.start()
    p.join(timeout=timeout)
    
    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError("Optimization timed out")
    
    result = res_queue.get()
    if isinstance(result, Exception):
        raise result
    return result

class Solver:
    def solve(self, problem: dict[str, Any]) -> dict[str, Any]:
        model_type = problem["model_type"]
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        
        if model_type == "polynomial":
            deg = problem["degree"]
            # Create Vandermonde matrix using iterative computation to avoid exponentiation
            n = len(x_data)
            vander = np.empty((n, deg+1))
            vander[:, deg] = 1.0  # x^0
            for i in range(deg-1, -1, -1):
                vander[:, i] = x_data * vander[:, i+1]
            params_opt, _, _, _ = np.linalg.lstsq(vander, y_data, rcond=None)
            return {"params": params_opt.tolist()}
        
        # For nonlinear models, use bounded optimization
        residual, guess, bounds = self._create_residual_function(problem)
        
        try:
            # Try with timeout (90% of allowed time)
            result = _run_optimization(residual, guess, bounds, timeout=9)
            params_opt = result.x
            if np.isnan(params_opt).any():
                raise RuntimeError("Invalid parameters")
            return {"params": params_opt.tolist()}
        except (TimeoutError, RuntimeError, ValueError):
            # Fallback to reference method with increased iteration limit
            residual_ref, guess_ref = self._create_reference_residual(problem)
            params_opt_ref, _, _, _, _ = leastsq(
                residual_ref, guess_ref, full_output=True, maxfev=20000
            )
            return {"params": params_opt_ref.tolist()}
        except:
            # Fallback to reference method
            residual_ref, guess_ref = self._create_reference_residual(problem)
            params_opt_ref, _, _, _, _ = leastsq(
                residual_ref, guess_ref, full_output=True, maxfev=10000
            )
            return {"params": params_opt_ref.tolist()}
    
    def _create_residual_function(
        self, problem: dict[str, Any]
    ) -> tuple[Callable, np.ndarray, tuple]:
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]
        
        if model_type == "exponential":
            def residual(p):
                a, b, c = p
                return y_data - (a * _safe_exp(b * x_data) + c)
            
            guess = np.array([1.0, 0.05, 0.0])
            bounds = ([-np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "logarithmic":
            # Robust initial guess using linear regression on log-transformed data
            x_min = np.min(x_data)
            shift = max(0, -x_min) + 1e-3
            log_x = np.log(x_data + shift)
            slope, intercept = np.polyfit(log_x, y_data, 1)
            
            def residual(p):
                a, b, c, d = p
                # Add small epsilon to avoid log(0)
                return y_data - (a * np.log(b * x_data + c + 1e-12) + d)
            
            guess = np.array([slope, 1.0, shift, intercept])
            # Constrain b and c to be positive
            bounds = ([-np.inf, 1e-12, 1e-12, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "sigmoid":
            def residual(p):
                a, b, c, d = p
                z = -b * (x_data - c)
                return y_data - (a / (1 + _safe_exp(z)) + d)
            
            guess = np.array([3.0, 0.5, np.median(x_data), 0.0])
            # Constrain a, b to be positive
            bounds = ([1e-12, 1e-12, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            return residual, guess, bounds
        
        elif model_type == "sinusoidal":
            # Use grid search for frequency if dataset is small
            n = len(x_data)
            y_mean = np.mean(y_data)
            y_centered = y_data - y_mean
            
            if n > 50:
                # Use FFT for larger datasets
                fft = np.fft.rfft(y_centered)
                freqs = np.fft.rfftfreq(n)
                idx = np.argmax(np.abs(fft[1:])) + 1
                freq = freqs[idx]
                b_guess = 2 * np.pi * freq * n / (np.max(x_data) - np.min(x_data))
            else:
                # Grid search for smaller datasets
                b_candidates = np.linspace(0.1, 10, 20)
                best_score = float('inf')
                for b in b_candidates:
                    # Simple phase estimation
                    phase = np.arctan2(np.sin(b * x_data).dot(y_centered),
                                 np.cos(b * x_data).dot(y_centered))
                    a = np.sqrt(np.mean((y_centered * np.sin(b * x_data + phase))**2 + 
                                (y_centered * np.cos(b * x_data + phase))**2))
                    residuals = y_centered - a * np.sin(b * x_data + phase)
                    score = np.sum(residuals**2)
                    if score < best_score:
                        best_score = score
                        b_guess = b
            
            # Simple phase estimation
            phase = np.arctan2(np.sin(b_guess * x_data).dot(y_centered),
                         np.cos(b_guess * x_data).dot(y_centered))
            a_guess = np.std(y_centered) * np.sqrt(2)
            
            guess = np.array([a_guess, b_guess, phase, y_mean])
            bounds = ([-np.inf, 1e-12, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf])
            
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.sin(b * x_data + c) + d)
            
            return residual, guess, bounds
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_reference_residual(
        self, problem: dict[str, Any]
    ) -> tuple[Callable, np.ndarray]:
        """Create residual function in reference style (without bounds)"""
        x_data = np.asarray(problem["x_data"])
        y_data = np.asarray(problem["y_data"])
        model_type = problem["model_type"]
        
        if model_type == "exponential":
            def residual(p):
                a, b, c = p
                return y_data - (a * _safe_exp(b * x_data) + c)
            guess = np.array([1.0, 0.05, 0.0])
        elif model_type == "logarithmic":
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.log(b * x_data + c + 1e-12) + d)
            guess = np.array([1.0, 1.0, 1.0, 0.0])
        elif model_type == "sigmoid":
            def residual(p):
                a, b, c, d = p
                return y_data - (a / (1 + _safe_exp(-b * (x_data - c))) + d)
            guess = np.array([3.0, 0.5, np.median(x_data), 0.0])
        elif model_type == "sinusoidal":
            def residual(p):
                a, b, c, d = p
                return y_data - (a * np.sin(b * x_data + c) + d)
            guess = np.array([2.0, 1.0, 0.0, 0.0])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        return residual, guess
EOF
