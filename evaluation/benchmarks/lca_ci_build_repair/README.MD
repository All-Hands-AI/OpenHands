# CI Builds Repair Benchmark Integration

This module integrates the CI Builds Repair benchmark developed by [JetBrains-Research](https://github.com/JetBrains-Research/lca-baselines/tree/main/ci-builds-repair/ci-builds-repair-benchmark).

For more information, refer to the [GitHub repository](https://github.com/JetBrains-Research/lca-baselines/tree/main/ci-builds-repair/ci-builds-repair-benchmark) and the associated [research paper](https://arxiv.org/abs/2406.11612).
See notice below for details

## Setup

Before running any scripts, make sure to configure the benchmark by setting up `config.yaml`.
This benchmark pushes to JetBrains' private GitHub repository. You will to request a `token_gh` provided by their team, to run this benchmark.

## Inference

To run inference with your model:

```bash
./evaluation/benchmarks/lca_ci_build_repair/scripts/run_infer.sh llm.yourmodel
```

## Evaluation

To evaluate the predictions:

```bash
./evaluation/benchmarks/lca_ci_build_repair/scripts/eval_infer.sh predictions_path_containing_output
```

## Results
The benchmark contains 68 instances, we skip instances #126 and #145, and only run 66 instances due to dockerization errors.

Due to running in live GitHub machines, the benchmark is sensitive to the date it is run. Even the golden patches in the dataset might present failures due to updates.
For example, on 2025-04-09, running the benchmark against the golden patches gave 57/67 successes, with 1 job left in the waiting list.

On 2025-04-10, running the benchmark full with OH and no oracle, 37 succeeded. That is 54% of the complete set of 68 instances and 64% of the 57 that succeed with golden patches.
