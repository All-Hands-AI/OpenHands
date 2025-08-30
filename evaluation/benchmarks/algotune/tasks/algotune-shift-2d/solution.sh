#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, Dict, List

import numpy as np
import scipy.ndimage as ndi

class Solver:
    def __init__(self) -> None:
        # Cubic spline interpolation with zero padding at boundaries
        self.order: int = 3
        self.mode: str = "constant"
        # Reusable buffers to reduce allocations across calls
        self._buf1: np.ndarray | None = None
        self._buf2: np.ndarray | None = None

    def _get_buf(self, shape: tuple[int, int]) -> np.ndarray:
        if self._buf1 is None or self._buf1.shape != shape:
            self._buf1 = np.empty(shape, dtype=np.float64, order="C")
        return self._buf1

    def _get_buf2(self, shape: tuple[int, int]) -> np.ndarray:
        if self._buf2 is None or self._buf2.shape != shape:
            self._buf2 = np.empty(shape, dtype=np.float64, order="C")
        return self._buf2

    @staticmethod
    def _integer_shift_to_out(src: np.ndarray, r: int, c: int, out: np.ndarray) -> None:
        """Integer shift with zero padding, writing into preallocated 'out'."""
        out.fill(0.0)
        nrows, ncols = src.shape

        i0 = max(0, -r)
        i1 = min(nrows, nrows - r)
        j0 = max(0, -c)
        j1 = min(ncols, ncols - c)

        if i1 > i0 and j1 > j0:
            out[i0 + r : i1 + r, j0 + c : j1 + c] = src[i0:i1, j0:j1]

    def solve(self, problem: Dict[str, Any], **kwargs) -> Dict[str, List[List[float]]]:
        """
        Shift a 2D image by a subpixel amount using cubic spline interpolation (order=3)
        and constant boundary mode (zero padding).
        """
        try:
            image = problem["image"]
            shift_vec = problem["shift"]

            # Ensure numpy float64 array for consistent and fast SciPy processing
            arr = np.asarray(image, dtype=np.float64, order="C")
            sr = float(shift_vec[0])
            sc = float(shift_vec[1])

            # Zero-shift fast path
            if sr == 0.0 and sc == 0.0:
                return {"shifted_image": list(arr)}

            order = self.order
            mode = self.mode

            # Exact integer-shift fast path (both axes)
            sr_int = float(sr).is_integer()
            sc_int = float(sc).is_integer()
            shape = arr.shape

            if sr_int and sc_int:
                out_int = self._get_buf(shape)
                self._integer_shift_to_out(arr, int(round(sr)), int(round(sc)), out_int)
                return {"shifted_image": list(out_int)}

            # One-axis integer fast paths: perform fractional shift first, then integer shift via slicing
            if sr_int and not sc_int:
                tmp = self._get_buf(shape)
                # fractional along columns only
                ndi.shift(
                    arr,
                    shift=(0.0, sc),
                    order=order,
                    mode=mode,
                    cval=0.0,
                    prefilter=True,
                    output=tmp,
                )
                out = self._get_buf2(shape)
                self._integer_shift_to_out(tmp, int(round(sr)), 0, out)
                return {"shifted_image": list(out)}

            if sc_int and not sr_int:
                tmp = self._get_buf(shape)
                # fractional along rows only
                ndi.shift(
                    arr,
                    shift=(sr, 0.0),
                    order=order,
                    mode=mode,
                    cval=0.0,
                    prefilter=True,
                    output=tmp,
                )
                out = self._get_buf2(shape)
                self._integer_shift_to_out(tmp, 0, int(round(sc)), out)
                return {"shifted_image": list(out)}

            # General subpixel shift via SciPy (cubic spline interpolation, constant padding)
            out = self._get_buf(shape)
            ndi.shift(
                arr,
                shift=(sr, sc),
                order=order,
                mode=mode,
                cval=0.0,
                prefilter=True,  # required for order > 1
                output=out,
            )

            # Return as list of row arrays to minimize Python-level conversions
            return {"shifted_image": list(out)}
        except Exception:
            # If any unexpected issue occurs, return empty as failure indicator
            return {"shifted_image": []}
EOF
