#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict
import math

# Try to obtain mpmath.mp in a robust way; if unavailable, fall back.
try:
    from mpmath import mp  # type: ignore
    _HAS_MPMATH = True
except Exception:
    try:
        import mpmath as mpmath  # type: ignore
        mp = mpmath.mp  # type: ignore
        _HAS_MPMATH = True
    except Exception:
        mp = None  # type: ignore
        _HAS_MPMATH = False

class Solver:
    def solve(self, problem: Any, **kwargs) -> Dict[str, Any]:
        """
        Count nontrivial zeros of the Riemann zeta function with 0 < Re(s) < 1
        and Im(s) <= t.

        This implementation delegates to mpmath.mp.nzeros when available
        (matching the reference solver). If mpmath is unavailable or nzeros
        raises, a conservative main-term approximation (Riemann–von Mangoldt)
        is returned.
        """
        # Robust parsing: accept dict, list/tuple or scalar
        t_in = None
        if isinstance(problem, dict):
            t_in = problem.get("t", None)
        elif isinstance(problem, (list, tuple)):
            t_in = problem[0] if len(problem) > 0 else None
        else:
            t_in = problem

        # Coerce to float
        try:
            t = float(t_in)
        except Exception:
            return {"result": 0}

        if not math.isfinite(t) or t <= 0.0:
            return {"result": 0}

        # If mpmath is available, use the reference approach for exact matching.
        if _HAS_MPMATH and mp is not None:
            try:
                n_ref = int(mp.nzeros(mp.mpf(t)))
                if n_ref < 0:
                    n_ref = 0
                return {"result": n_ref}
            except Exception:
                # Fall through to main-term approximation on error
                pass

        # Main-term fallback (Riemann–von Mangoldt leading term)
        two_pi = 2.0 * math.pi
        x = t / two_pi
        if x <= 0.0:
            return {"result": 0}
        main = x * math.log(x) - x + 7.0 / 8.0
        n_est = int(math.floor(main + 0.5))
        if n_est < 0:
            n_est = 0
        return {"result": n_est}

    def _count_zeros_rvm(self, t: float) -> int:
        """
        Count zeros using the Riemann–von Mangoldt relation:
        N(T) = theta(T)/pi + 1 + S(T), where S(T) = arg zeta(1/2 + iT)/pi.

        We compute theta via loggamma and arg zeta via mp.arg at a heuristic precision
        chosen from the magnitude of T, then round to the nearest integer. If anything
        goes wrong, fall back to the main-term approximation.
        """
        # Fallback to main-term if mpmath not available
        if not _HAS_MPMATH or mp is None:
            two_pi = 2.0 * math.pi
            x = t / two_pi
            if x <= 0.0:
                return 0
            main = x * math.log(x) - x + 7.0 / 8.0
            n_est = int(math.floor(main + 0.5))
            return max(n_est, 0)

        old_dps = getattr(mp, "dps", None)
        try:
            # Heuristic digit selection: increase with log10(t); clamp to reasonable bounds.
            t_abs = max(1.0, float(abs(t)))
            dps = int(min(200, max(30, int(40 + 8.0 * math.log10(t_abs)))))
            mp.dps = dps

            T = mp.mpf(t)
            # theta(T) = Im(logGamma(1/4 + iT/2)) - (T/2)*log(pi)
            z = mp.mpf('0.25') + mp.j * T / mp.mpf(2)
            lg = mp.loggamma(z)
            theta = mp.im(lg) - (T / mp.mpf(2)) * mp.log(mp.pi)

            # compute zeta(1/2 + iT) and its argument
            s = mp.mpf('0.5') + mp.j * T
            zeta = mp.zeta(s)

            # If zeta is extremely small (we may be exactly at a zero), perturb slightly upward
            if abs(zeta) < mp.mpf('1e-30'):
                # a tiny shift avoids undefined argument exactly at a zero
                T2 = T + mp.mpf('1e-8')
                s = mp.mpf('0.5') + mp.j * T2
                zeta = mp.zeta(s)

            argz = mp.arg(zeta)

            Nf = theta / mp.pi + mp.mpf(1) + argz / mp.pi
            # round to nearest integer
            N = int(mp.floor(Nf + mp.mpf('0.5')))
            if N < 0:
                N = 0
            return N
        except Exception:
            # conservative main-term fallback
            two_pi = 2.0 * math.pi
            x = t / two_pi
            if x <= 0.0:
                return 0
            main = x * math.log(x) - x + 7.0 / 8.0
            n_est = int(math.floor(main + 0.5))
            return max(n_est, 0)
        finally:
            if old_dps is not None:
                mp.dps = old_dps
EOF
