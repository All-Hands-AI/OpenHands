# AlgoTune Benchmark

AlgoTune is a benchmark for evaluating AI agents' ability to optimize and accelerate algorithmic implementations across a wide range of computational tasks.

## Overview

The benchmark consists of over 100 diverse algorithmic tasks spanning:
- **Numerical Computing**: Matrix operations, linear algebra, numerical integration
- **Machine Learning**: Clustering, dimensionality reduction, optimization
- **Graph Algorithms**: Path finding, graph theory, network analysis
- **Signal Processing**: FFT, convolution, filtering
- **Cryptography**: Encryption, hashing, security primitives
- **Optimization Problems**: Linear programming, constraint satisfaction
- **Statistical Methods**: Hypothesis testing, density estimation

Each task requires implementing a `Solver` class with a `solve()` method that must outperform a reference implementation while maintaining correctness.

## Task Structure

Each task directory (`tasks/algotune-*`) contains:
- `problem_statement.txt`: Detailed description, input/output format, and reference implementation
- `evaluator.py`: Validation logic to check solution correctness
- `solution.sh`: Script template for the solver
- `test_outputs.py`: Test cases and evaluation harness
- `run-tests.sh`: Test runner script

## Usage

### Running the Benchmark

Use the main evaluation script:

```bash
poetry run python evaluation/benchmarks/algotune/adapter/run_adapter.py --output-path evaluation/benchmarks/algotune/tasks

poetry run python evaluation/benchmarks/algotune/run_infer.py \
  --agent-cls CodeActAgent \
  --llm-config llm.gpt-5 \
  --optim_task all \
  --max-iterations 500 \
  --eval-num-workers 7
```

Or use the convenience script:

```bash
scripts/run_infer.sh <model_config> <commit_hash> <agent> <optim_task> <max_iter> <num_workers>
```

### Available Tasks

Run with `--optim_task all` to execute all tasks, or specify individual tasks:
- `--optim_task algotune-kmeans` - K-means clustering optimization
- `--optim_task algotune-svd` - Singular Value Decomposition
- ...and many more (see `tasks/` directory)

## Evaluation Metrics

Each task is evaluated on:
1. **Correctness**: Solution must pass all validation tests
2. **Speedup**: Performance improvement over reference implementation (target: 10x)

## Environment

The benchmark runs in a Docker container with extensive scientific computing libraries:
- NumPy, SciPy, scikit-learn
- JAX, PyTorch, TensorFlow
- CVXPY, OR-Tools, PuLP
- Numba, Cython, Pythran
- NetworkX, FAISS, and more

## Implementation Requirements

Each solver must implement:

```python
class Solver:
    def solve(self, problem: dict, **kwargs) -> Any:
        # Optimized implementation
        pass
```

The `solve` method should:
- Accept a problem dictionary with task-specific inputs
- Return the solution in the specified format
- Be significantly faster than the reference implementation
- Maintain mathematical correctness and numerical stability

## Development

To add a new task:
1. Create a directory in `tasks/algotune-<task-name>`
2. Include all required files (problem_statement.txt, evaluator.py, etc.)
3. Define clear input/output specifications
4. Provide a reference implementation and validation logic
5. Add comprehensive test cases

## Results

Evaluation results are saved in JSONL format with detailed metrics:
- Runtime performance comparisons
- Validation outcomes
- Error analysis
- Solution quality scores

## License

This benchmark is part of the OpenHands evaluation framework. See the main project for licensing information.
