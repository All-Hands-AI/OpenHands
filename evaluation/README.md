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
- analysis
  - devin_eval_analysis.ipynb: notebook analyzing devin's outputs