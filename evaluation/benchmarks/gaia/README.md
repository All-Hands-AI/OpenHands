# GAIA Evaluation

This folder contains evaluation harness for evaluating agents on the [GAIA benchmark](https://arxiv.org/abs/2311.12983).

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run the evaluation

We are using the GAIA dataset hosted on [Hugging Face](https://huggingface.co/datasets/gaia-benchmark/GAIA).
Please accept the terms and make sure to have logged in on your computer by `huggingface-cli login` before running the evaluation.

Following is the basic command to start the evaluation. Here we are evaluating on the validation set for the `2023_all` split. You can adjust `./evaluation/benchmarks/gaia/scripts/run_infer.sh` to change the subset you want to evaluate on.

```bash
./evaluation/benchmarks/gaia/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [gaia_subset]
# e.g., ./evaluation/benchmarks/gaia/scripts/run_infer.sh eval_gpt4_1106_preview 0.6.2 CodeActAgent 300
```

where `model_config` is mandatory, while `git-version`, `agent`, `eval_limit` and `gaia_subset` are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`, defaulting to `gpt-3.5-turbo`

- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances, defaulting to all instances.

- `gaia_subset`, GAIA benchmark has multiple subsets: `2023_level1`, `2023_level2`, `2023_level3`, `2023_all`, defaulting to `2023_level1`.

For example,

```bash
./evaluation/benchmarks/gaia/scripts/run_infer.sh eval_gpt4_1106_preview 0.6.2 CodeActAgent 10
```

## Get score

Then you can get stats by running the following command:

```bash
python ./evaluation/benchmarks/gaia/get_score.py \
--file <path_to/output.json>
```
