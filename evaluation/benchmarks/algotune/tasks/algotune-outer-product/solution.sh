#!/bin/bash

cat > /workspace/solver.py << 'EOF'
import jax
import jax.numpy as jnp

class Solver:
    def __init__(self):
        # Pre-compile the JIT function during init (doesn't count towards runtime)
        @jax.jit
        def outer_product(v1, v2):
            return v1[:, None] * v2
        self.outer_product = outer_product
    
    def solve(self, problem):
        vec1, vec2 = problem
        # Convert to JAX arrays and compute
        v1 = jnp.asarray(vec1)
        v2 = jnp.asarray(vec2)
        return self.outer_product(v1, v2)
EOF
