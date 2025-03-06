# SWE-Bench Evaluation with OpenHands SWE-Bench Docker Image

This folder contains the evaluation harness that we built on top of the original [SWE-Bench benchmark](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)).

**UPDATE (2/18/2025): We now support running SWE-Gym using the same evaluation harness here. For more details, checkout [this README](./SWE-Gym.md).

**UPDATE (7/1/2024): We now support the official SWE-Bench dockerized evaluation as announced [here](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md).**

The evaluation consists of three steps:

1. Environment setup: [install python environment](../../README.md#development-environment) and [configure LLM config](../../README.md#configure-openhands-and-your-llm).
2. [Run inference](#run-inference-on-swe-bench-instances): Generate a edit patch for each Github issue
3. [Evaluate patches using SWE-Bench docker](#evaluate-generated-patches)

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference (Rollout) on SWE-Bench Instances: Generate Patch from Problem Statement

### Running Locally with Docker

Make sure your Docker daemon is running, and you have ample disk space (at least 200-500GB, depends on the SWE-Bench set you are running on) for the instance-level docker image.

When the `run_infer.sh` script is started, it will automatically pull the relevant SWE-Bench images.
For example, for instance ID `django_django-11011`, it will try to pull our pre-build docker image `sweb.eval.x86_64.django_s_django-11011` from DockerHub.
This image will be used create an OpenHands runtime image where the agent will operate on.

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 500 100 1 princeton-nlp/SWE-bench_Verified test
```

where `model_config` is mandatory, and the rest are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the entire SWE-bench_Lite test set (300 issues). Note:
in order to use `eval_limit`, you must also set `agent`.
- `max_iter`, e.g. `20`, is the maximum number of iterations for the agent to run. By
default, it is set to 30.
- `num_workers`, e.g. `3`, is the number of parallel workers to run the evaluation. By
default, it is set to 1.
- `dataset`, a huggingface dataset name. e.g. `princeton-nlp/SWE-bench`, `princeton-nlp/SWE-bench_Lite`, or `princeton-nlp/SWE-bench_Verified`, specifies which dataset to evaluate on.
- `dataset_split`, split for the huggingface dataset. e.g., `test`, `dev`. Default to `test`.

> [!CAUTION]
> Setting `num_workers` larger than 1 is not officially tested, YMMV.

There is also one optional environment variable you can set.

```bash
export USE_HINT_TEXT=true # if you want to use hint text in the evaluation. Default to false. Ignore this if you are not sure.
```

Let's say you'd like to run 10 instances using `llm.eval_gpt4_1106_preview` and CodeActAgent,

then your command would be:

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 10
```

### Running in parallel with RemoteRuntime

OpenHands Remote Runtime is currently in beta (read [here](https://runtime.all-hands.dev/) for more details), it allows you to run rollout in parallel in the cloud, so you don't need a powerful machine to run evaluation.

Fill out [this form](https://docs.google.com/forms/d/e/1FAIpQLSckVz_JFwg2_mOxNZjCtr7aoBFI2Mwdan3f75J_TrdMS1JV2g/viewform) to apply if you want to try this out!

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example - This runs evaluation on CodeActAgent for 300 instances on "princeton-nlp/SWE-bench_Lite"'s test set, with max 30 iteration per instances, with 16 number of workers running in parallel
ALLHANDS_API_KEY="YOUR-API-KEY" RUNTIME=remote SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" \
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval HEAD CodeActAgent 300 30 16 "princeton-nlp/SWE-bench_Lite" test
```

To clean-up all existing runtime you've already started, run:

```bash
ALLHANDS_API_KEY="YOUR-API-KEY" ./evaluation/utils/scripts/cleanup_remote_runtime.sh
```

### Specify a subset of tasks to run infer

If you would like to specify a list of tasks you'd like to benchmark on, you could
create a `config.toml` under `./evaluation/benchmarks/swe_bench/` folder, and put a list
attribute named `selected_ids`, e.g.

```toml
selected_ids = ['sphinx-doc__sphinx-8721', 'sympy__sympy-14774', 'scikit-learn__scikit-learn-10508']
```

Then only these tasks (rows whose `instance_id` is in the above list) will be evaluated.
In this case, `eval_limit` option applies to tasks that are in the `selected_ids` list.

After running the inference, you will obtain a `output.jsonl` (by default it will be saved to `evaluation/evaluation_outputs`).

## Evaluate Generated Patches

### Run evaluation with official SWE-Bench harness (Recommend if you have local disk space)

With `output.jsonl` file, you can run `eval_infer.sh` to evaluate generated patches, and produce a fine-grained report.
**This evaluation is performed using the official dockerized evaluation announced [here](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md).**

> [!NOTE]
> This process will automatically download docker images from SWE-Bench official docker hub, please make sure you have enough disk space!


```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL [instance_id] [dataset_name] [split]

# Example
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The script now accepts optional arguments:

- `instance_id`: Specify a single instance to evaluate (optional)
- `dataset_name`: The name of the dataset to use (default: `"princeton-nlp/SWE-bench_Lite"`)
- `split`: The split of the dataset to use (default: `"test"`)

For example, to evaluate a specific instance with a custom dataset and split:

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL instance_123 princeton-nlp/SWE-bench test
```

> You can also pass in a JSONL with [SWE-Bench format](https://github.com/princeton-nlp/SWE-bench/blob/main/tutorials/evaluation.md#-creating-predictions) to `./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh`, where each line is a JSON of `{"model_patch": "XXX", "model_name_or_path": "YYY", "instance_id": "ZZZ"}`.

The final results will be saved to `evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/` with the following files/directory:

- `README.md`: a report showing what are the instances that passed, failed, etc.
- `report.json`: a JSON file that contains keys like `"resolved_ids"` pointing to instance IDs that are resolved by the agent.
- `logs/`: a directory of test logs

### Run evaluation with `RemoteRuntime`

OpenHands Remote Runtime is currently in beta (read [here](https://runtime.all-hands.dev/) for more details), it allows you to run rollout in parallel in the cloud, so you don't need a powerful machine to run evaluation.
Fill out [this form](https://docs.google.com/forms/d/e/1FAIpQLSckVz_JFwg2_mOxNZjCtr7aoBFI2Mwdan3f75J_TrdMS1JV2g/viewform) to apply if you want to try this out!

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer_remote.sh [output.jsonl filepath] [num_workers]

# Example - This evaluates patches generated by CodeActAgent on Llama-3.1-70B-Instruct-Turbo on "princeton-nlp/SWE-bench_Lite"'s test set, with 16 number of workers running in parallel
ALLHANDS_API_KEY="YOUR-API-KEY" RUNTIME=remote SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" \
evaluation/benchmarks/swe_bench/scripts/eval_infer_remote.sh evaluation/evaluation_outputs/outputs/swe-bench-lite/CodeActAgent/Llama-3.1-70B-Instruct-Turbo_maxiter_30_N_v1.9-no-hint/output.jsonl 16 "princeton-nlp/SWE-bench_Lite" "test"
```

To clean-up all existing runtimes that you've already started, run:

```bash
ALLHANDS_API_KEY="YOUR-API-KEY" ./evaluation/utils/scripts/cleanup_remote_runtime.sh
```
