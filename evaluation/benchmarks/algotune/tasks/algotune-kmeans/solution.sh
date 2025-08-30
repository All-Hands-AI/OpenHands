#!/bin/bash

cat > /workspace/solver.py << 'EOF'
from typing import Any, List
import numpy as np
import faiss

class Solver:
    def solve(self, problem: dict[str, Any], **kwargs) -> List[int]:
        """
        Fast KMeans clustering using FAISS (faiss-cpu). Falls back to sklearn if needed.
        Input:
            problem: dict with keys "X" (n x d list/array) and "k" (int clusters)
        Returns:
            List[int]: cluster assignment for each sample.
        """
        X = np.asarray(problem.get("X", []), dtype=np.float32)
        k = int(problem.get("k", 0))
        if k <= 0 or X.ndim != 2 or X.shape[0] == 0:
            return [0] * (X.shape[0] if X.ndim == 2 else 0)
        if k == 1:
            return [0] * X.shape[0]
        try:
            d = X.shape[1]
            # faster: reduce iterations and single redo
            kmeans = faiss.Kmeans(d, k, niter=3, nredo=1, verbose=False)
            kmeans.train(X)
            _, labels = kmeans.index.search(X, 1)
            return labels.reshape(-1).tolist()
        except Exception:
            try:
                from sklearn.cluster import KMeans
                kmeans2 = KMeans(n_clusters=k, n_init='auto', random_state=0).fit(X)
                return kmeans2.labels_.tolist()
            except Exception:
                return [0] * X.shape[0]
EOF
