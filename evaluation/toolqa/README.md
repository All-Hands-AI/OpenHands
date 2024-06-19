# ToolQA Evaluation with OpenDevin

This folder contains an evaluation harness we built on top of the original [ToolQA](https://github.com/night-chen/ToolQA) ([paper](https://arxiv.org/pdf/2306.13304)).

## Setup Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local development environment for OpenDevin.

## Configure OpenDevin and your LLM

Run `make setup-config` to set up the `config.toml` file if it does not exist at the root of the workspace.

## Run Inference on ToolQA Instances

Make sure your Docker daemon is running, then run this bash script:

```bash
bash evaluation/toolqa/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [dataset] [hardness] [wolfram_alpha_appid]
```

where `model_config` is mandatory, while all other arguments are optional.

`model_config`, e.g. `llm`, is the config group name for your
LLM settings, as defined in your `config.toml`.

`git-version`, e.g. `head`, is the git commit hash of the OpenDevin version you would
like to evaluate. It could also be a release tag like `0.6.2`.

`agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

`eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances.
By default, the script evaluates 1 instance.

`dataset`, the dataset from ToolQA to evaluate from. You could choose from `agenda`, `airbnb`, `coffee`, `dblp`, `flight`, `gsm8k`, `scirex`, `yelp` for dataset. The default is `coffee`.

`hardness`, the hardness to evaluate. You could choose from `easy` and `hard`. The default is `easy`.

`wolfram_alpha_appid` is an optional argument. When given `wolfram_alpha_appid`, the agent will be able to access Wolfram Alpha's APIs.

Note: in order to use `eval_limit`, you must also set `agent`; in order to use `dataset`, you must also set `eval_limit`; in order to use `hardness`, you must also set `dataset`.

Let's say you'd like to run 10 instances using `llm` and CodeActAgent on `coffee` `easy` test,
then your command would be:

```bash
bash evaluation/toolqa/scripts/run_infer.sh llm CodeActAgent 10 coffee easy
```
