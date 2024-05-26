# Evaluation

This folder contains code and resources to run experiments and evaluations.

## Logistics
To better organize the evaluation folder, we should follow the rules below:
  - Each subfolder contains a specific benchmark or experiment. For example, `evaluation/swe_bench` should contain
all the preprocessing/evaluation/analysis scripts.
  - Raw data and experimental records should not be stored within this repo.
    - For model outputs, they should be stored at [this huggingface space](https://huggingface.co/spaces/OpenDevin/evaluation) for visualization.
  - Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.

## Supported Benchmarks

- SWE-Bench: [`evaluation/swe_bench`](./swe_bench)
- HumanEvalFix: [`evaluation/humanevalfix`](./humanevalfix)
- GAIA: [`evaluation/gaia`](./gaia)
- Entity deduction Arena (EDA): [`evaluation/EDA`](./EDA)

### Result Visualization

Check [this huggingface space](https://huggingface.co/spaces/OpenDevin/evaluation) for visualization of existing experimental results.


### Upload your results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results to our hosted huggingface repo via PR following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
