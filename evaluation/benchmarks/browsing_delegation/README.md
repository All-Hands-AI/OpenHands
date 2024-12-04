# Browsing Delegation Evalution

Some of OpenHands's agent supports agent delegation action, for example, CodeActAgent can delegate browsing tasks to BrowsingAgent.

This evaluation tests whether CodeActAgent can correctly delegate the instruction from WebArena and MiniWob benchmark to the BrowsingAgent.
If so, the browsing performance upper-bound of CodeActAgent will be the performance of BrowsingAgent.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference

```bash
./evaluation/benchmarks/browsing_delegation/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
# e.g., ./evaluation/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview_llm HEAD CodeActAgent 300
```

where `model_config` is mandatory, while `agent` and `eval_limit` are optional.

`model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

`git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

`agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

`eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances.
