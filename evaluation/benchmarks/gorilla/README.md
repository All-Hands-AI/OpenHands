# Gorilla APIBench Evaluation with OpenHands

This folder contains evaluation harness we built on top of the original [Gorilla APIBench](https://github.com/ShishirPatil/gorilla) ([paper](https://arxiv.org/pdf/2305.15334)).

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on APIBench Instances

Make sure your Docker daemon is running, then run this bash script:

```bash
./evaluation/benchmarks/gorilla/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [hubs]
```

where `model_config` is mandatory, while all other arguments are optional.

`model_config`, e.g. `llm`, is the config group name for your
LLM settings, as defined in your `config.toml`.

`git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

`agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

`eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances.
By default, the script evaluates 1 instance.

`hubs`, the hub from APIBench to evaluate from. You could choose one or more from `torch` or `th` (which is abbreviation of torch), `hf` (which is abbreviation of huggingface), and `tf` (which is abbreviation of tensorflow),  for `hubs`. The default is `hf,torch,tf`.

Note: in order to use `eval_limit`, you must also set `agent`; in order to use `hubs`, you must also set `eval_limit`.

For example,

```bash
./evaluation/benchmarks/gorilla/scripts/run_infer.sh llm 0.6.2 CodeActAgent 10 th
```
