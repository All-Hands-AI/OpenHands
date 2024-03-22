# Evaluation

This folder contains code and resources to run experiments and evaluations.

## Logistics
To better organize the evaluation folder, we should follow the rules below:
  - Each subfolder contains a specific benchmark or experiment. For example, `evaluation/SWE-bench` should contain
all the preprocessing/evaluation/analysis scripts.
  - Raw data and experimental records should not be stored within this repo (e.g. Google Drive or Hugging Face Datasets).
  - Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.

## Tasks
### SWE-bench
- notebooks
  - `devin_eval_analysis.ipynb`: notebook analyzing devin's outputs
- scripts
  - `prepare_devin_outputs_for_evaluation.py`: script fetching and converting [devin's output](https://github.com/CognitionAI/devin-swebench-results/tree/main) into the desired json file for evaluation.
    - usage: `python prepare_devin_outputs_for_evaluation.py <setting>` where setting can be `passed`, `failed` or `all`
- resources
  - Devin's outputs processed for evaluations is available on [Huggingface](https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output)
    - get predictions that passed the test: `wget https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output/raw/main/devin_swe_passed.json`
    - get all predictions `wget https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output/raw/main/devin_swe_outputs.json`

See [`SWE-bench/README.md`](./SWE-bench/README.md) for more details on how to run SWE-Bench for evaluation.
