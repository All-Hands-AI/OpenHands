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

## Evaluate Generated Patches

After running the inference described in the previous section, you will obtain a `output.jsonl` (by default it will save to `evaluation/evaluation_outputs`). Then you can run this one line script to evaluate generated patches, and produce a fine-grained report:

If you want to evaluate existing results, you should first run this to clone existing outputs

```bash
git clone https://huggingface.co/spaces/OpenDevin/evaluation evaluation/evaluation_outputs
```

Then you can run the following:
```bash
# ./evaluation/humanevalfix/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL
# For example:
./evaluation/humanevalfix/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/humanevalfix/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The final results will be saved to `evaluation/evaluation_outputs/outputs/humanevalfix/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.merged.jsonl`.

They should look something like below (TODO):

```json
TODO
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
