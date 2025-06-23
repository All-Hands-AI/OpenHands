# SWE-Bench Evaluation with OpenHands SWE-Bench Docker Image

This folder contains the evaluation harness that we built on top of the original [SWE-Bench benchmark](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)).

**UPDATE (6/15/2025): We now support running SWE-bench-Live evaluation (see the paper [here](https://arxiv.org/abs/2505.23419))! For how to run it, checkout [this README](./SWE-bench-Live.md).**

**UPDATE (5/26/2025): We now support running interactive SWE-Bench evaluation (see the paper [here](https://arxiv.org/abs/2502.13069))! For how to run it, checkout [this README](./SWE-Interact.md).**

**UPDATE (4/8/2025): We now support running SWT-Bench evaluation! For more details, checkout [the corresponding section](#SWT-Bench-Evaluation).**

**UPDATE (03/27/2025): We now support SWE-Bench multimodal evaluation! Simply use "princeton-nlp/SWE-bench_Multimodal" as the dataset name in the `run_infer.sh` script to evaluate on multimodal instances.**

**UPDATE (2/18/2025): We now support running SWE-Gym using the same evaluation harness here. For more details, checkout [this README](./SWE-Gym.md).**

**UPDATE (7/1/2024): We now support the official SWE-Bench dockerized evaluation as announced [here](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md).**

The evaluation consists of three steps:

1. Environment setup: [install python environment](../../README.md#development-environment) and [configure LLM config](../../README.md#configure-openhands-and-your-llm).
2. [Run inference](#run-inference-on-swe-bench-instances): Generate a edit patch for each Github issue
3. [Evaluate patches using SWE-Bench docker](#evaluate-generated-patches)

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference (Rollout) on SWE-Bench Instances: Generate Patch from Problem Statement

> [!NOTE]
> **Iterative Evaluation Protocol**
>
> We have an iterative approach for more stable and reproducible results:
> - For each instance, we attempt to generate a solution up to 3 times
> - Each attempt continues until either:
>   1. The agent successfully produces a patch with `AgentFinishAction`, or
>   2. The attempt reaches the maximum iteration limit
> - If an attempt fails, we retry with a fresh attempt (up to the 3-attempt maximum)
> - If your LLM config has temperature=0, we will automatically use temperature=0.1 for the 2nd and 3rd attempts
>
> To enable this iterative protocol, set `export ITERATIVE_EVAL_MODE=true`


### Running Locally with Docker

Make sure your Docker daemon is running, and you have ample disk space (at least 200-500GB, depends on the SWE-Bench set you are running on) for the instance-level docker image.

When the `run_infer.sh` script is started, it will automatically pull the relevant SWE-Bench images.
For example, for instance ID `django_django-11011`, it will try to pull our pre-build docker image `sweb.eval.x86_64.django_s_django-11011` from DockerHub.
This image will be used create an OpenHands runtime image where the agent will operate on.

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split] [n_runs] [mode]

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
default, it is set to 100.
- `num_workers`, e.g. `3`, is the number of parallel workers to run the evaluation. By
default, it is set to 1.
- `dataset`, a huggingface dataset name. e.g. `princeton-nlp/SWE-bench`, `princeton-nlp/SWE-bench_Lite`, `princeton-nlp/SWE-bench_Verified`, or `princeton-nlp/SWE-bench_Multimodal`, specifies which dataset to evaluate on.
- `dataset_split`, split for the huggingface dataset. e.g., `test`, `dev`. Default to `test`.

- `n_runs`, e.g. `3`, is the number of times to run the evaluation. Default is 1.
- `mode`, e.g. `swt`, `swt-ci`, or `swe`, specifies the evaluation mode. Default is `swe`.

> [!CAUTION]
> Setting `num_workers` larger than 1 is not officially tested, YMMV.

There are also optional environment variables you can set:

```bash
# Use hint text in the evaluation (default: false)
export USE_HINT_TEXT=true # Ignore this if you are not sure.

# Specify a condenser configuration for memory management (default: NoOpCondenser)
export EVAL_CONDENSER=summarizer_for_eval # Name of the condenser config group in config.toml
```

Let's say you'd like to run 10 instances using `llm.eval_gpt4_1106_preview` and CodeActAgent,

then your command would be:

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 10
```

For multimodal evaluation, you can use:

```bash
# Example for running multimodal SWE-Bench evaluation
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval_gpt4_vision HEAD CodeActAgent 10 100 1 princeton-nlp/SWE-bench_Multimodal test
```

### Running in parallel with RemoteRuntime

OpenHands Remote Runtime is currently in beta (read [here](https://runtime.all-hands.dev/) for more details), it allows you to run rollout in parallel in the cloud, so you don't need a powerful machine to run evaluation.

Fill out [this form](https://docs.google.com/forms/d/e/1FAIpQLSckVz_JFwg2_mOxNZjCtr7aoBFI2Mwdan3f75J_TrdMS1JV2g/viewform) to apply if you want to try this out!

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example - This runs evaluation on CodeActAgent for 300 instances on "princeton-nlp/SWE-bench_Lite"'s test set, with max 100 iteration per instances, with 16 number of workers running in parallel
ALLHANDS_API_KEY="YOUR-API-KEY" RUNTIME=remote SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" \
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval HEAD CodeActAgent 300 100 16 "princeton-nlp/SWE-bench_Lite" test
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
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Lite/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The script now accepts optional arguments:

- `instance_id`: Specify a single instance to evaluate (optional)
- `dataset_name`: The name of the dataset to use (default: `"princeton-nlp/SWE-bench_Lite"`)
- `split`: The split of the dataset to use (default: `"test"`)
- `environment`: The environment to use for patch evaluation (default: `"local"`). You can set it to
  `"modal"` to use [official SWE-Bench support](https://github.com/swe-bench/SWE-bench/blob/main/docs/assets/evaluation.md#%EF%B8%8F-evaluation-with-modal) for running evaluation on Modal.

For example, to evaluate a specific instance with a custom dataset and split:

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL instance_123 princeton-nlp/SWE-bench test
```

> You can also pass in a JSONL with [SWE-Bench format](https://github.com/SWE-bench/SWE-bench/blob/main/assets/evaluation.md#-creating-predictions) to `./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh`, where each line is a JSON of `{"model_patch": "XXX", "model_name_or_path": "YYY", "instance_id": "ZZZ"}`.

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
evaluation/benchmarks/swe_bench/scripts/eval_infer_remote.sh evaluation/evaluation_outputs/outputs/swe-bench-lite/CodeActAgent/Llama-3.1-70B-Instruct-Turbo_maxiter_100_N_v1.9-no-hint/output.jsonl 16 "princeton-nlp/SWE-bench_Lite" "test"
```

To clean-up all existing runtimes that you've already started, run:

```bash
ALLHANDS_API_KEY="YOUR-API-KEY" ./evaluation/utils/scripts/cleanup_remote_runtime.sh
```

## SWT-Bench Evaluation

[SWT-Bench](https://swtbench.com/) ([paper](https://arxiv.org/abs/2406.12952)) is a benchmark for evaluating the capability of LLMs at creating unit tests. It is performed on the same instances as SWE-Bench, but requires a separate evaluation harness to capture coverage and issue reproduction. We therefore detail below how to leverage the inference script in this folder to run inference on SWT-Bench and how to use the SWT-Bench evaluation harness to evaluate them.

### Run inference on SWT-Bench

To run inference on SWT-Bench, you can use the same `run_infer.sh` script as described for evaluation on plain SWE-Bench. The only differences is that you need to specify the `mode` parameter to `swt` or `swt-ci` when running the script. For example, to run inference on SWT-Bench Verified, run the following command:

```bash
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [swe-dataset] test 1 swt

# Example - This runs evaluation on CodeActAgent for 500 instances on "SWT-bench_Verified"'s test set (corresponding to SWE-bench_Verified), with max 100 iteration per instances, with 1 number of workers running in parallel
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.eval_gpt4o-2024-11-20 HEAD CodeActAgent 500 100 1 princeton-nlp/SWE-bench_Verified test 1 swt
```

The two modes `swt` and `swt-ci` have the following effect:
- `swt`: This mode will change the prompt to instruct the agent to generate reproducing test cases instead of resolving the issue.
- `swt-ci`: In addition to the changes by `swt`, this mode sets up the CI environment by i) pre-installing the environment in the docker image, such that the test framework can be executed without errors and ii) telling the model the exact command to run the test framework.

### Run evaluation for SWT-bench

The evaluation of these results is done leveraging [the SWT-Bench evaluation harness](https://github.com/logic-star-ai/swt-bench/tree/master).

#### Extracting results into SWT-Bench harness format
In order to run evaluation of the obtained inference results in the SWT-Bench harness, we transform the results to a format that the SWT-Bench evaluation harness expects.

```bash
python3 evaluation/benchmarks/swe_bench/scripts/swtbench/convert.py --prediction_file [output.jsonl] > [output_swt.jsonl]

# Example
python3 evaluation/benchmarks/swe_bench/scripts/swtbench/convert.py --prediction_file "evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/gpt-4o-2024-11-20_maxiter_100_N_v0.31.0-no-hint-swt-run_1/output.jsonl" > OpenHands-gpt-4o-2024-11-20.jsonl
```

#### Running the results in SWT-Bench

Next, we run the [SWT-Bench evaluation harness](https://github.com/logic-star-ai/swt-bench/tree/master) with these results.
First set-up and validate the setup as described in the harness [here](https://github.com/logic-star-ai/swt-bench/tree/master?tab=readme-ov-file#-set-up).
Then, run the evaluation with the following command:

```bash
# Example
python3 -m src.main \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path <pathTo>/OpenHands-gpt-4o-2024-11-20.jsonl \
    --max_workers 12 \
    --run_id OpenHands-CodeAct-gpt-4o-2024-11-20  --patch_types vanilla  --build_mode api
```

The results of the evaluation can be obtained by running the reporting script of the harness.

```bash
# Example
python -m src.report run_instance_swt_logs/OpenHands-CodeAct-gpt-4o-2024-11-20/OpenHands__CodeActAgent__gpt-4o-2024-11-20 --dataset verified
```
