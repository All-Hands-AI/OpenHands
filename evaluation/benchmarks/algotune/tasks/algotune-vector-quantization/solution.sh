#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import numpy as np
import faiss
import json
from typing import Any, Dict

class Solver:
    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the Vector Quantization problem using optimized Faiss implementation.

        :param problem: A dictionary representing the Vector Quantization problem.
        :return: A dictionary with keys:
                 "centroids": 2D list representing the k centroids/codewords found.
                 "assignments": 1D list indicating which centroid each input vector is assigned to.
                 "quantization_error": The mean squared error of the quantization.
        """
        # Handle string input
        if isinstance(problem, str):
            problem = json.loads(problem)
            
        # Extract problem parameters and convert to float32 for Faiss
        vectors = np.array(problem["vectors"], dtype=np.float32)
        k = problem["k"]
        dim = vectors.shape[1]

        # Try to use GPU if available for faster computation
        try:
            # Check if GPU is available
            ngpus = faiss.get_num_gpus()
            if ngpus > 0:
                # Use GPU for training
                kmeans = faiss.Kmeans(dim, k, niter=100, verbose=False, gpu=True)
            else:
                kmeans = faiss.Kmeans(dim, k, niter=100, verbose=False)
        except:
            # Fallback to CPU if GPU setup fails
            kmeans = faiss.Kmeans(dim, k, niter=100, verbose=False)
            
        kmeans.train(vectors)
        centroids = kmeans.centroids

        # Use the assignment from kmeans directly if available for better performance
        try:
            distances, assignments = kmeans.index.search(vectors, 1)
        except:
            # Fallback to creating a new index
            index = faiss.IndexFlatL2(dim)
            index.add(centroids)
            distances, assignments = index.search(vectors, 1)

        # Calculate quantization error
        quantization_error = float(np.mean(distances))

        return {
            "centroids": centroids.tolist(),
            "assignments": assignments.flatten().tolist(),
            "quantization_error": quantization_error,
        }
EOF
