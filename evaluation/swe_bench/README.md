# SWE-Bench Evaluation with OpenDevin SWE-Bench Docker Image


This folder contains evaluation harness we built on top of the original [SWE-Bench benchmark](https://www.swebench.com/) ([paper](https://arxiv.org/abs/2310.06770)). We create [a fork of SWE-Bench](https://github.com/OpenDevin/OD-SWE-bench.git) mostly build on top of [the original repo](https://github.com/princeton-nlp/SWE-bench) and [containerized](#opendevin-swe-bench-docker-image) it for easy evaluation.

## OpenDevin SWE-Bench Docker Image

In [OpenDevin-SWE-Bench fork](https://github.com/OpenDevin/OD-SWE-bench.git) (mostly from [original repo](https://github.com/princeton-nlp/SWE-bench) with some fixes), we try to pre-build the **testbed** (i.e., code of the repository we want the agent to edit) AND the **conda environment**, so that in evaluation (inference) time, we can directly leverage existing environments for effecienct evaluation.

**We pack everything you need for SWE-Bench evaluation into one, gigantic, docker image.** To use it:

```bash
docker pull ghcr.io/opendevin/eval-swe-bench:full-v1.0
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
use_host_network = true
ssh_hostname = "localhost"
sandbox_timeout = 120
# SWEBench eval specific
run_as_devin = false

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

```bash
python3 evaluation/swe_bench/swe_env_box.py
```

If you get to the interactive shell successfully, it means success!

## Run Inference on SWE-Bench Instances

```bash
./evaluation/swe_bench/scripts/run_infer.sh eval_gpt4_1106_preview
```

You can replace `eval_gpt4_1106_preview` with any model you setted up in `config.toml`.


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
