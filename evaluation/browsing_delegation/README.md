# Browsing Delegation Evalution

Some of OpenDevin's agent supports agent delegation action, for example, CodeActAgent can delegate browsing tasks to BrowsingAgent.

This evaluation tests whether CodeActAgent can correctly delegate the instruction from WebArena and MiniWob benchmark to the BrowsingAgent.
If so, the browsing performance upper-bound of CodeActAgent will be the performance of BrowsingAgent.


## Setup Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to set up a local development environment for OpenDevin.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
ssh_hostname = "localhost"

[sandbox]
box_type = "ssh"
timeout = 120

# SWEBench eval specific
use_host_network = false
run_as_devin = false
enable_auto_lint = true
max_budget_per_task = 4 # 4 USD

# TODO: Change these to the model you want to evaluate
[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

## Run Inference

```bash
./evaluation/browsing_delegation/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
# e.g., ./evaluation/swe_bench/scripts/run_infer.sh eval_gpt4_1106_preview_llm HEAD CodeActAgent 300
```

where `model_config` is mandatory, while `agent` and `eval_limit` are optional.

`model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

`git-version`, e.g. `HEAD`, is the git commit hash of the OpenDevin version you would
like to evaluate. It could also be a release tag like `0.6.2`.

`agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

`eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the entire SWE-bench_Lite test set (300 issues). Note:
in order to use `eval_limit`, you must also set `agent`.

## View Result Summary

If you just want to know the resolve rate, and/or a summary of what tests pass and what don't, you could run

```bash
poetry run python ./evaluation/swe_bench/scripts/summarise_results.py <path_to_report_json_file>
# e.g. poetry run python ./evaluation/swe_bench/scripts/summarise_results.py ./evaluation/evaluation_outputs/outputs/swe_bench_lite/CodeActSWEAgent/gpt-4o-2024-05-13_maxiter_50_N_v1.5-no-hint/report.json
```
