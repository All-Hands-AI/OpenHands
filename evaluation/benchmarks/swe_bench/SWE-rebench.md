# SWE-rebench

<p align="center">
<a href="https://arxiv.org/abs/2505.20411">📃 Paper</a>
•
<a href="https://huggingface.co/datasets/nebius/SWE-rebench">🤗 HuggingFace</a>
•
<a href="https://swe-rebench.com/leaderboard">📊 Leaderboard</a>
</p>

SWE-rebench is a large-scale dataset for verifiable software engineering tasks.
It comes in **two datasets**:

* **[`nebius/SWE-rebench-leaderboard`](https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard)** – updatable benchmark used for [leaderboard evaluation](https://swe-rebench.com/leaderboard).
* **[`nebius/SWE-rebench`](https://huggingface.co/datasets/nebius/SWE-rebench)** – full dataset with **21,302 tasks**, suitable for training or large-scale offline evaluation.

This document explains how to run OpenHands on SWE-rebench, using the leaderboard split as the main example.
To run on the full dataset, simply replace the dataset name.


## Setting Up

Set up your development environment and configure your LLM provider by following the [SWE-bench README](README.md) in this directory.


## Running Inference

Use the existing SWE-bench inference script, changing the dataset to `nebius/SWE-rebench-leaderboard` and selecting the split (`test` for leaderboard submission):

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    llm.your_llm HEAD CodeActAgent 30 50 1 nebius/SWE-rebench-leaderboard test
```

Arguments:

* `llm.your_llm` – your model configuration key
* `HEAD` – commit reference for reproducibility
* `CodeActAgent` – agent type
* `10` – number of examples to evaluate
* `50` – maximum iterations per task (increase if needed)
* `1` – number of workers
* `nebius/SWE-rebench-leaderboard` – Hugging Face dataset name
* `test` – dataset split

**Tip:** To run on the **full 21k dataset**, replace `nebius/SWE-rebench-leaderboard` with `nebius/SWE-rebench`.


## Evaluating Results

After inference completes, evaluate using the [SWE-bench-fork evaluation harness](https://github.com/SWE-rebench/SWE-bench-fork).

1. Convert the OpenHands output to SWE-bench evaluation format:

```bash
python evaluation/benchmarks/swe_bench/scripts/live/convert.py \
  --output_jsonl path/to/evaluation/output.jsonl > preds.jsonl
```

2. Clone the SWE-bench-fork repo (https://github.com/SWE-rebench/SWE-bench-fork) and follow its README to install dependencies.


3. Run the evaluation using the fork:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name nebius/SWE-rebench-leaderboard \
    --split test \
    --predictions_path preds.jsonl \
    --max_workers 10 \
    --run_id openhands
```


## Citation

```bibtex
@article{badertdinov2025swerebench,
  title={SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents},
  author={Badertdinov, Ibragim and Golubev, Alexander and Nekrashevich, Maksim and Shevtsov, Anton and Karasik, Simon and Andriushchenko, Andrei and Trofimova, Maria and Litvintseva, Daria and Yangel, Boris},
  journal={arXiv preprint arXiv:2505.20411},
  year={2025}
}
```
