# AgentBench Evaluation

This folder contains evaluation harness for evaluating agents on the [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688). We currently only support running on the `osbench` subset.

## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local development environment and LLM.

## Start the evaluation

```bash
./evaluation/agent_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
```

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the entire SWE-bench_Lite test set (300 issues). Note:
in order to use `eval_limit`, you must also set `agent`.


Following is the basic command to start the evaluation.

You can update the arguments in the script `evaluation/agent_bench/scripts/run_infer.sh`, such as `--max-iterations`, `--eval-num-workers` and so on.

- `--agent-cls`, the agent to use. For example, `CodeActAgent`.
- `--llm-config`: the LLM configuration to use. For example, `eval_gpt4_1106_preview`.
- `--max-iterations`: the number of iterations to run the evaluation. For example, `30`.
- `--eval-num-workers`: the number of workers to use for evaluation. For example, `5`.
- `--eval-n-limit`: the number of examples to evaluate. For example, `100`.

```bash
./evaluation/agent_bench/scripts/run_infer.sh eval_gpt35_turbo HEAD CodeActAgent 1
```
