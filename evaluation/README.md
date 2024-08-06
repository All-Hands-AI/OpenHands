# Evaluation

This folder contains code and resources to run experiments and evaluations.

## Logistics
To better organize the evaluation folder, we should follow the rules below:
  - Each subfolder contains a specific benchmark or experiment. For example, `evaluation/swe_bench` should contain
all the preprocessing/evaluation/analysis scripts.
  - Raw data and experimental records should not be stored within this repo.
    - For model outputs, they should be stored at [this huggingface space](https://huggingface.co/spaces/OpenDevin/evaluation) for visualization.
  - Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.

## Supported Benchmarks

- SWE-Bench: [`evaluation/swe_bench`](./swe_bench)
- ML-Bench: [`evaluation/ml_bench`](./ml_bench)
- HumanEvalFix: [`evaluation/humanevalfix`](./humanevalfix)
- GAIA: [`evaluation/gaia`](./gaia)
- Entity deduction Arena (EDA): [`evaluation/EDA`](./EDA)
- MINT: [`evaluation/mint`](./mint)
- AgentBench: [`evaluation/agent_bench`](./agent_bench)
- BIRD: [`evaluation/bird`](./bird)
- LogicReasoning: [`evaluation/logic_reasoning`](./logic_reasoning)

## Setup

### Development environment
Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to set up a local development environment for OpenDevin.

### Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. You can copy from `config.template.toml` if it is easier for you.

Add the configuration for your LLM:

```toml
# TODO: Change these to the model you want to evaluate
[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```


### Result Visualization

Check [this huggingface space](https://huggingface.co/spaces/OpenDevin/evaluation) for visualization of existing experimental results.


### Upload your results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results to our hosted huggingface repo via PR following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
