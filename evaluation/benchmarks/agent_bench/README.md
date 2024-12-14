# AgentBench Evaluation

This folder contains evaluation harness for evaluating agents on the [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688). We currently only support running on the `osbench` subset.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Start the evaluation

```bash
./evaluation/benchmarks/agent_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
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

You can update the arguments in the script `evaluation/benchmarks/agent_bench/scripts/run_infer.sh`, such as `--max-iterations`, `--eval-num-workers` and so on.

- `--agent-cls`, the agent to use. For example, `CodeActAgent`.
- `--llm-config`: the LLM configuration to use. For example, `eval_gpt4_1106_preview`.
- `--max-iterations`: the number of iterations to run the evaluation. For example, `30`.
- `--eval-num-workers`: the number of workers to use for evaluation. For example, `5`.
- `--eval-n-limit`: the number of examples to evaluate. For example, `100`.

```bash
./evaluation/benchmarks/agent_bench/scripts/run_infer.sh eval_gpt35_turbo HEAD CodeActAgent 1
```

## Run with Remote Runtime (experimental)

You can run the evaluation using a remote runtime instead of a local Docker container. This is useful when you want to run the evaluation in a cloud environment or when you don't have Docker installed locally.

To use the remote runtime, set the following environment variables:

```bash
# Required environment variables
export ALLHANDS_API_KEY="your-api-key"  # Contact the team to get an API key
export RUNTIME=remote
export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev"

# Run the evaluation
./evaluation/benchmarks/agent_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 1
```

The remote runtime will build a container image and run the evaluation in a cloud environment. The results will be saved locally in the same way as when running with a local runtime.
