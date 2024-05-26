# SWE-Bench Evaluation with OpenDevin SWE-Bench Docker Image


This folder contains evaluation harness we built on top of the original [SWE-Bench benchmark](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)). We create [a fork of SWE-Bench](https://github.com/OpenDevin/OD-SWE-bench.git) mostly build on top of [the original repo](https://github.com/princeton-nlp/SWE-bench) and [containerized](#opendevin-swe-bench-docker-image) it for easy evaluation.

## Setup Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.


## OpenDevin SWE-Bench Docker Image

In [OpenDevin-SWE-Bench fork](https://github.com/OpenDevin/OD-SWE-bench.git) (mostly from [original repo](https://github.com/princeton-nlp/SWE-bench) with some fixes), we try to pre-build the **testbed** (i.e., code of the repository we want the agent to edit) AND the **conda environment**, so that in evaluation (inference) time, we can directly leverage existing environments for effecienct evaluation.

**We pack everything you need for SWE-Bench evaluation into one, gigantic, docker image.** To use it:

```bash
docker pull ghcr.io/opendevin/eval-swe-bench:full-v1.2.1
```

The Docker image contains several important directories:
- `/swe_util/OD-SWE-bench`: root directory for the OD-SWE-bench repository
- `/swe_util/eval_data`: director to eval data
  - `/swe_util/eval_data/eval_logs/`: evaluation logs
  - `/swe_util/eval_data/eval_temp/`: temporary folder for the evaluation process
  - `/swe_util/eval_data/instances/`: swe-bench raw instances
  - `/swe_util/eval_data/outputs/`: model or agent outputs
  - `/swe_util/eval_data/testbed_logs/`: logs for testbed building
  - `/swe_util/eval_data/testbeds/`: directory for all testbeds
- `/swe_util/miniforge3/`: directory for miniforge3

To reproduce how we pack the image, check [this doc](./BUILD_TESTBED_AND_ENV.md).

NOTE: We only support SWE-Bench lite for now. But modifying our existing scripts for full SWE-Bench should be quite straight forward.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
sandbox_container_image = "ghcr.io/opendevin/sandbox:latest"
sandbox_type = "ssh"
ssh_hostname = "localhost"
sandbox_timeout = 120

# SWEBench eval specific
use_host_network = false
run_as_devin = false
enable_auto_lint = true

# TODO: Change these to the model you want to evaluate
[eval_gpt4_1106_preview]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[eval_some_openai_compatible_model]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

## Test if your environment works

Make sure your Docker daemon is running, and you have pulled the `eval-swe-bench:full-v1.2`
docker image. Then run this python script:

```bash
poetry run python evaluation/swe_bench/swe_env_box.py
```

If you get to the interactive shell successfully, it means your environment works!
If you see an error, please make sure your `config.toml` contains all
`SWEBench eval specific` settings as shown in the previous section.

## Run Inference on SWE-Bench Instances

```bash
./evaluation/swe_bench/scripts/run_infer.sh [model_config] [agent] [eval_limit]
# e.g., ./evaluation/swe_bench/scripts/run_infer.sh eval_gpt4_1106_preview CodeActAgent 300
```

where `model_config` is mandatory, while `agent` and `eval_limit` are optional.

`model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

`agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

`eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the entire SWE-bench_Lite test set (300 issues). Note:
in order to use `eval_limit`, you must also set `agent`.

Let's say you'd like to run 10 instances using `eval_gpt4_1106_preview` and CodeActAgent,
then your command would be:

```bash
./evaluation/swe_bench/scripts/run_infer.sh eval_gpt4_1106_preview CodeActAgent 10
```

If you would like to specify a list of tasks you'd like to benchmark on, you could
create a `config.toml` under `./evaluation/swe_bench/` folder, and put a list
attribute named `selected_ids`, e.g.

```toml
selected_ids = ['sphinx-doc__sphinx-8721', 'sympy__sympy-14774', 'scikit-learn__scikit-learn-10508']
```

Then only these tasks (rows whose `instance_id` is in the above list) will be evaluated.
In this case, `eval_limit` option applies to tasks that are in the `selected_ids` list.

## Evaluate Generated Patches

After running the inference described in the previous section, you will obtain a `output.jsonl` (by default it will save to `evaluation/evaluation_outputs`). Then you can run this one line script to evaluate generated patches, and produce a fine-grained report:

If you want to evaluate existing results, you should first run this to clone existing outputs

```bash
git clone https://huggingface.co/spaces/OpenDevin/evaluation evaluation/evaluation_outputs
```

Then you can run the following:
```bash
# ./evaluation/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL
# For example:
./evaluation/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The final results will be saved to `evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.merged.jsonl`.

It will contains an additional field `fine_grained_report` (see example below) compared to the `output.jsonl` from the previous inference stage.

```json
"fine_grained_report": {
  "gold_tests": {
    "FAIL_TO_PASS": "[\"tests/test_ext_viewcode.py::test_viewcode_epub_default\"]",
    "PASS_TO_PASS": "[\"tests/test_ext_viewcode.py::test_viewcode_epub_enabled\", \"tests/test_ext_viewcode.py::test_linkcode\", \"tests/test_ext_viewcode.py::test_local_source_files\"]"
  },
  "generated": true,
  "with_logs": true,
  "applied": true,
  "test_errored": false,
  "test_timeout": false,
  "resolved": true,
  "log_parse": {
    "tests/test_ext_viewcode.py::test_viewcode_epub_default": "PASSED",
    "tests/test_ext_viewcode.py::test_viewcode_epub_enabled": "PASSED",
    "tests/test_ext_viewcode.py::test_linkcode": "PASSED",
    "tests/test_ext_viewcode.py::test_local_source_files": "PASSED",
    "tests/test_ext_viewcode.py::test_viewcode": "FAILED"
  },
  "eval_report": {
    "FAIL_TO_PASS": {
      "success": [
        "tests/test_ext_viewcode.py::test_viewcode_epub_default"
      ],
      "failure": []
    },
    "PASS_TO_PASS": {
      "success": [
        "tests/test_ext_viewcode.py::test_viewcode_epub_enabled",
        "tests/test_ext_viewcode.py::test_linkcode",
        "tests/test_ext_viewcode.py::test_local_source_files"
      ],
      "failure": []
    },
    "FAIL_TO_FAIL": {
      "success": [],
      "failure": []
    },
    "PASS_TO_FAIL": {
      "success": [],
      "failure": []
    }
  }
}
```

Please refer to [EVAL_PATCH.md](./EVAL_PATCH.md) if you want to learn more about how to evaluate patches that are already generated (e.g., not by OpenDevin).

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
