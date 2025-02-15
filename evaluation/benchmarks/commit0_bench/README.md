# Commit0 Evaluation with OpenHands

This folder contains the evaluation harness that we built on top of the original [Commit0](https://commit-0.github.io/) ([paper](TBD)).

The evaluation consists of three steps:

1. Environment setup: [install python environment](../../README.md#development-environment), [configure LLM config](../../README.md#configure-openhands-and-your-llm).
2. [Run Evaluation](#run-inference-on-commit0-instances): Generate a edit patch for each Commit0 Repo, and get the evaluation results

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## OpenHands Commit0 Instance-level Docker Support

OpenHands supports using the Commit0 Docker for **[inference](#run-inference-on-commit0-instances).
This is now the default behavior.

## Run Inference on Commit0 Instances

Make sure your Docker daemon is running, and you have ample disk space (at least 200-500GB, depends on the Commit0 set you are running on) for the [instance-level docker image](#openhands-commit0-instance-level-docker-support).

When the `run_infer.sh` script is started, it will automatically pull the `lite` split in Commit0. For example, for instance ID `commit-0/minitorch`, it will try to pull our pre-build docker image `wentingzhao/minitorch` from DockerHub. This image will be used create an OpenHands runtime image where the agent will operate on.

```bash
./evaluation/benchmarks/commit0_bench/scripts/run_infer.sh [repo_split] [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example
./evaluation/benchmarks/commit0_bench/scripts/run_infer.sh lite llm.eval_sonnet HEAD CodeActAgent 16 100 8 wentingzhao/commit0_combined test
```

where `model_config` is mandatory, and the rest are optional.

- `repo_split`, e.g. `lite`, is the split of the Commit0 dataset you would like to evaluate on. Available options are `lite`, `all` and each individual repo.
- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the `lite` split of the Commit0 dataset (16 repos). Note:
in order to use `eval_limit`, you must also set `agent`.
- `max_iter`, e.g. `20`, is the maximum number of iterations for the agent to run. By
default, it is set to 30.
- `num_workers`, e.g. `3`, is the number of parallel workers to run the evaluation. By
default, it is set to 1.
- `dataset`, a huggingface dataset name. e.g. `wentingzhao/commit0_combined`, specifies which dataset to evaluate on.
- `dataset_split`, split for the huggingface dataset. Notice only `test` is supported for Commit0.

Note that the `USE_INSTANCE_IMAGE` environment variable is always set to `true` for Commit0.

Let's say you'd like to run 10 instances using `llm.eval_sonnet` and CodeActAgent,

then your command would be:

```bash
./evaluation/benchmarks/commit0_bench/scripts/run_infer.sh lite llm.eval_sonnet HEAD CodeActAgent 10 30 1 wentingzhao/commit0_combined test
```

### Run Inference on `RemoteRuntime` (experimental)

This is in limited beta. Contact Xingyao over slack if you want to try this out!

```bash
./evaluation/benchmarks/commit0_bench/scripts/run_infer.sh [repo_split] [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example - This runs evaluation on CodeActAgent for 10 instances on "wentingzhao/commit0_combined"'s test set, with max 30 iteration per instances, with 1 number of workers running in parallel
ALLHANDS_API_KEY="YOUR-API-KEY" RUNTIME=remote SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" EVAL_DOCKER_IMAGE_PREFIX="docker.io/wentingzhao" \
./evaluation/benchmarks/commit0_bench/scripts/run_infer.sh lite llm.eval_sonnet HEAD CodeActAgent 10 30 1 wentingzhao/commit0_combined test
```

To clean-up all existing runtime you've already started, run:

```bash
ALLHANDS_API_KEY="YOUR-API-KEY" ./evaluation/utils/scripts/cleanup_remote_runtime.sh
```

### Specify a subset of tasks to run infer

If you would like to specify a list of tasks you'd like to benchmark on, you just need to pass selected repo through `repo_split` option.
