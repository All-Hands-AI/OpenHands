# Logic Reasoning Evaluation

This folder contains evaluation harness for evaluating agents on the logic reasoning benchmark [ProntoQA](https://github.com/asaparov/prontoqa) and [ProofWriter](https://allenai.org/data/proofwriter).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
ssh_hostname = "localhost"
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

## Run Inference on logic_reasoning
The following code will run inference on the first example of the ProntoQA dataset with model gpt-4o.
```bash
./evaluation/logic_reasoning/scripts/run_infer.sh ProntoQA gpt-4o 1
```
