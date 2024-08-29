# SWE-Bench Evaluation with OpenHands SWE-Bench Docker Image

This folder contains the evaluation harness that we built on top of the original [SWE-Bench benchmark](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)).

**UPDATE (7/1/2024): We now support the official SWE-Bench dockerized evaluation as announced [here](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md).**

The evaluation consists of three steps:

1. Environment setup: [install python environment](../README.md#development-environment), [configure LLM config](../README.md#configure-openhands-and-your-llm), and [pull docker](#openhands-swe-bench-instance-level-docker-support).
2. [Run inference](#run-inference-on-swe-bench-instances): Generate a edit patch for each Github issue
3. [Evaluate patches using SWE-Bench docker](#evaluate-generated-patches)

## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local development environment and LLM.

## OpenHands SWE-Bench Instance-level Docker Support

OpenHands now support using the [official evaluation docker](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md) for both **[inference](#run-inference-on-swe-bench-instances) and [evaluation](#evaluate-generated-patches)**.
This is now the default behavior.

### Download Docker Images

**(Recommended for reproducibility)** If you have extra local space (e.g., 100GB), you can try pull the [instance-level docker images](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md#choosing-the-right-cache_level) we've prepared by running:

```bash
evaluation/swe_bench/scripts/docker/pull_all_eval_docker.sh instance
```

If you want to save disk space a bit (e.g., with ~50GB free disk space), while speeding up the image pre-build process, you can pull the environment-level docker images:

```bash
evaluation/swe_bench/scripts/docker/pull_all_eval_docker.sh env
```

## Run Inference on SWE-Bench Instances

Make sure your Docker daemon is running, and you have pulled the [instance-level docker image](#openhands-swe-bench-instance-level-docker-support).

```bash
./evaluation/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers]
# e.g., ./evaluation/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 300
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

There are also two optional environment variables you can set.
```
export USE_HINT_TEXT=true # if you want to use hint text in the evaluation. Default to false. Ignore this if you are not sure.
export USE_INSTANCE_IMAGE=true # if you want to use instance-level docker images. Default to true
```

Let's say you'd like to run 10 instances using `llm.eval_gpt4_1106_preview` and CodeActAgent,

then your command would be:

```bash
./evaluation/swe_bench/scripts/run_infer.sh llm.eval_gpt4_1106_preview HEAD CodeActAgent 10
```

**Evaluate on `RemoteRuntime` (alpha)** (contact Xingyao over slack if you want to try this out!)
```bash
SANDBOX_API_KEY="CONTACT-XINGYAO-TO-GET-A-TESTING-API-KEY" RUNTIME=remote EVAL_DOCKER_IMAGE_PREFIX="us-docker.pkg.dev/evaluation-428620/swe-bench-images" ./evaluation/swe_bench/scripts/run_infer.sh llm.eval HEAD CodeActAgent 300
```
Multi-processing is still WIP.

### Specify a subset of tasks to run infer

If you would like to specify a list of tasks you'd like to benchmark on, you could
create a `config.toml` under `./evaluation/swe_bench/` folder, and put a list
attribute named `selected_ids`, e.g.

```toml
selected_ids = ['sphinx-doc__sphinx-8721', 'sympy__sympy-14774', 'scikit-learn__scikit-learn-10508']
```

Then only these tasks (rows whose `instance_id` is in the above list) will be evaluated.
In this case, `eval_limit` option applies to tasks that are in the `selected_ids` list.

After running the inference, you will obtain a `output.jsonl` (by default it will be saved to `evaluation/evaluation_outputs`).

## Evaluate Generated Patches

With `output.jsonl` file, you can run `eval_infer.sh` to evaluate generated patches, and produce a fine-grained report.

**This evaluation is performed using the official dockerized evaluation announced [here](https://github.com/princeton-nlp/SWE-bench/blob/main/docs/20240627_docker/README.md).**

> If you want to evaluate existing results, you should first run this to clone existing outputs
>```bash
>git clone https://huggingface.co/spaces/OpenDevin/evaluation evaluation/evaluation_outputs
>```

NOTE, you should have already pulled the instance-level OR env-level docker images following [this section](#openhands-swe-bench-instance-level-docker-support).

Then you can run the following:

```bash
# ./evaluation/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL [instance_id] [dataset_name] [split]
# For example:
./evaluation/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The script now accepts optional arguments:
- `instance_id`: Specify a single instance to evaluate (optional)
- `dataset_name`: The name of the dataset to use (default: `"princeton-nlp/SWE-bench_Lite"`)
- `split`: The split of the dataset to use (default: `"test"`)

For example, to evaluate a specific instance with a custom dataset and split:

```bash
./evaluation/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL instance_123 princeton-nlp/SWE-bench test
```

> You can also pass in a JSONL with [SWE-Bench format](https://github.com/princeton-nlp/SWE-bench/blob/main/tutorials/evaluation.md#-creating-predictions) to `./evaluation/swe_bench/scripts/eval_infer.sh`, where each line is a JSON of `{"model_patch": "XXX", "model_name_or_path": "YYY", "instance_id": "ZZZ"}`.

The final results will be saved to `evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/` with the following files/directory:

- `README.md`: a report showing what are the instances that passed, failed, etc.
- `report.json`: a JSON file that contains keys like `"resolved_ids"` pointing to instance IDs that are resolved by the agent.
- `logs/`: a directory of test logs

## Visualize Results

First you need to clone `https://huggingface.co/spaces/OpenDevin/evaluation` and add your own running results from openhands into the `outputs` of the cloned repo.

```bash
git clone https://huggingface.co/spaces/OpenDevin/evaluation
```

**(optional) setup streamlit environment with conda**:
```bash
cd evaluation
conda create -n streamlit python=3.10
conda activate streamlit
pip install -r requirements.txt
```

**run the visualizer**:
Then, in a separate Python environment with `streamlit` library, you can run the following:

```bash
# Make sure you are inside the cloned `evaluation` repo
conda activate streamlit # if you follow the optional conda env setup above
streamlit run 0_📊_OpenHands_Benchmark.py --server.port 8501 --server.address 0.0.0.0
```

Then you can access the SWE-Bench trajectory visualizer at `localhost:8501`.

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
