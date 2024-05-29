# GAIA Evaluation

This folder contains evaluation harness for evaluating agents on the [GAIA benchmark](https://arxiv.org/abs/2311.12983).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Run the evaluation
We are using the GAIA dataset hosted on [Hugging Face](https://huggingface.co/datasets/gaia-benchmark/GAIA).
Please accept the terms and make sure to have logged in on your computer by `huggingface-cli login` before running the evaluation.

Following is the basic command to start the evaluation. Here we are evaluating on the validation set for the `2023_all` split. You can adjust `./evaluation/gaia/scripts/run_infer.sh` to change the subset you want to evaluate on.

```bash
./evaluation/gaia/scripts/run_infer.sh [model_config] [agent] [eval_limit] [gaia_subset]
# e.g., ./evaluation/gaia/scripts/run_infer.sh eval_gpt4_1106_preview CodeActAgent 300
```

where `model_config` is mandatory, while `agent`, `eval_limit` and `gaia_subset` are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`, defaulting to `gpt-3.5-turbo`

- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances, defaulting to all instances.

- `gaia_subset`, GAIA benchmark has multiple subsets: `2023_level1`, `2023_level2`, `2023_level3`, `2023_all`, defaulting to `2023_level1`.

Let's say you'd like to run 10 instances using `eval_gpt4_1106_preview` and CodeActAgent,
then your command would be:

```bash
./evaluation/gaia/scripts/run_infer.sh eval_gpt4_1106_preview CodeActAgent 10
```

## Get score

Then you can get stats by running the following command:
```bash
python ./evaluation/gaia/get_score.py \
--file <path_to/output.json>
```
