# Easy SWE-Bench Evaluation in the OpenDevin SWE-Bench Docker Image

The documentation for this section is currently **under construction** and is expected to be completed and merged to `main` within the week. Subscribe to [this pr](https://github.com/OpenDevin/OpenDevin/pull/1468) to track its progress.

## OpenDevin SWE-Bench Docker Image

In [OpenDevin-SWE-Bench fork](https://github.com/OpenDevin/OD-SWE-bench.git), we try to pre-build the **testbed** (i.e., code of the repository we want the agent to edit) AND the **conda environment**, so that in evaluation (inference) time, we can directly leverage existing environments for effecienct evaluation.

**We pack everything you need for SWE-Bench evaluation into one, gigantic, docker image.** To use it:

```bash
docker pull ghcr.io/xingyaoww/eval-swe-bench-all:lite-v1.1
```

To reproduce how we pack the image, check [this doc](./BUILD_TESTBED_AND_ENV.md).

NOTE: We only support SWE-Bench lite for now. But modifying our existing scripts for full SWE-Bench should be quite straight forward.

## Test if your environment works

```bash
python3 evaluation/swe_bench/swe_env_box.py
```

If you get to the interactive shell successfully, it means success!

## Run Inference on SWE-Bench Instances

```bash
python3 evaluation/swe_bench/run_infer.py \
  --agent-cls CodeActAgent \
  --model-name gpt-4-turbo-2024-04-09 \
  --max-iterations 50 \
  --llm-temperature 0.0 \
  --max-chars 10000000 \
  --eval-num-workers 8
```


## Evaluate Generated Patches

### Evaluate Model Generated Patches

#### Setting Up the Environment

Before evaluating model-generated patches, you need to set up the Docker environment. Run the following command to instantiate the Docker container:

```shell
docker run -it \
-v DIR_TO_YOUR_PATCH_FILES_ON_HOST:/swe_bench_output \
ghcr.io/xingyaoww/eval-swe-bench-all:lite-v1.0 /bin/bash
```

Running the Evaluation
Inside the Docker container, execute the following commands to prepare the environment and run the evaluation script:

```shell
export MINICONDA3=/swe_util/miniconda3
export OD_SWE_BENCH=/swe_util/OD-SWE-bench
export EVAL_DATA_DIR=/swe_util/eval_data
cd /swe_util && ./get_model_report.sh --output-file /swe_bench_output/YOUR_OUTPUT_FILE_NAME \
--model-name YOUR_MODEL_NAME \
--dataset swe-bench-lite-test
```

### Evaluate Agent Generated Patches

#### Setting Up the Environment

The setup process for evaluating agent-generated patches is identical to that for model-generated patches. Ensure you have the Docker container running with the following command:

```shell
docker run -it \
-v DIR_TO_YOUR_PATCH_FILES_ON_HOST:/swe_bench_output \
ghcr.io/opendevin/eval-swe-bench-all:lite-v1.0 /bin/bash
```

#### Running the Evaluation

Within the Docker container, use the following commands to set the environment and execute the evaluation script:

```shell
export MINICONDA3=/swe_util/miniconda3
export OD_SWE_BENCH=/swe_util/OD-SWE-bench
export EVAL_DATA_DIR=/swe_util/eval_data
cd /swe_util && ./get_agent_report.sh --output-file /swe_bench_output/YOUR_OUTPUT_FILE_NAME \
--model-or-agent-name YOUR_AGENT_NAME \
--dataset swe-bench-lite-test
```
