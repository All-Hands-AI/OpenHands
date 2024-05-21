# HumanEvalFix Evaluation with OpenDevin

Implements evaluation of agents on HumanEvalFix from the HumanEvalPack benchmark introduced in [OctoPack: Instruction Tuning Code Large Language Models](https://arxiv.org/abs/2308.07124). Please see https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack.py for the reference implementation used in the paper.

## Setup Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.

In addition, evaluation requires the `evaluate` package installable via:
```bash
pip install evaluate
```

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
ssh_hostname = "localhost"

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

## Run Inference on HumanEvalFix

```bash
./evaluation/humanevalfix/scripts/run_infer.sh eval_gpt4_1106_preview
```

You can replace `eval_gpt4_1106_preview` with any model you set up in `config.toml`.

