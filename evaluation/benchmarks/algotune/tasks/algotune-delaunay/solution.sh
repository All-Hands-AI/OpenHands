#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
try:
    from scipy.spatial import _qhull as qhull  # type: ignore
except ImportError:
    from scipy.spatial.qhull import _Qhull as qhull  # type: ignore

class Solver:
    def solve(self, problem, **kwargs):
        pts = np.asarray(problem["points"])
        
        # Create Qhull object for Delaunay triangulation with optimized options
        try:
            qh = qhull(pts, b'd', qhull_options=b'Qbb Qc Qz Qx QJ Qt')
            qh.process()
            
            # Get simplices
            simplices = qh.get_simplices()
            
            # Optimized convex hull extraction
            ch_facets = qh.get_convex_hull_facets()
            # Pre-allocate array for faster processing
            # Vectorized convex hull extraction
            facet_indices = np.array([facet[0] for facet in ch_facets], dtype=np.int32)
            convex_hull = np.sort(facet_indices, axis=1)
        except Exception:
            # Optimized fallback to standard implementation
            try:
                from scipy.spatial import Delaunay
            except ImportError:
                from scipy.spatial.qhull import Delaunay
            tri = Delaunay(pts, qhull_options="Qbb Qc Qz Qx")
            simplices = tri.simplices
            convex_hull = np.sort(tri.convex_hull, axis=1)
        
        return {
            "simplices": simplices,
            "convex_hull": convex_hull
        }
EOF
