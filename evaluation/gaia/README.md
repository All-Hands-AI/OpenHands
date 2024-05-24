# GAIA Evaluation

This folder contains evaluation harness for evaluating agents on the [GAIA benchmark](https://arxiv.org/abs/2311.12983).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation
We are using the GAIA dataset hosted on [Hugging Face](https://huggingface.co/datasets/gaia-benchmark/GAIA).
Please accept the terms and make sure to have logged in on your computer by `huggingface-cli login` before running the evaluation.

Following is the basic command to start the evaluation. Here we are only evaluating the first instance of the validation set for the 2023_level1 split.

You can remove the `--eval-n-limit 1` argument to evaluate all instances in that subset. Or change `--data-split` `--data-split` to test other splits.
```bash
python ./evaluation/gaia/run_infer.py \
--level 2023_level1 \
--data-split validation \
--eval-n-limit 1 \
--max-iterations 30 \
---eval-output-dir <output_dir>
```

Then you can get stats by running the following command:
```bash
python ./evaluation/gaia/get_score.py \
--file <path_to/output.json>
```
