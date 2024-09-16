# Evaluation

This folder contains code and resources to run experiments and evaluations.

## Logistics

To better organize the evaluation folder, we should follow the rules below:

- Each subfolder contains a specific benchmark or experiment. For example, `evaluation/swe_bench` should contain
all the preprocessing/evaluation/analysis scripts.
- Raw data and experimental records should not be stored within this repo.
- For model outputs, they should be stored at [this huggingface space](https://huggingface.co/spaces/OpenHands/evaluation) for visualization.
- Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.

## Supported Benchmarks

To learn more about how to integrate your benchmark into OpenHands, check out [tutorial here](https://docs.all-hands.dev/modules/usage/how-to/evaluation-harness).

### Software Engineering

- SWE-Bench: [`evaluation/swe_bench`](./swe_bench)
- HumanEvalFix: [`evaluation/humanevalfix`](./humanevalfix)
- BIRD: [`evaluation/bird`](./bird)
- BioCoder: [`evaluation/ml_bench`](./ml_bench)
- ML-Bench: [`evaluation/ml_bench`](./ml_bench)
- APIBench: [`evaluation/gorilla`](./gorilla/)
- ToolQA: [`evaluation/toolqa`](./toolqa/)
- AiderBench: [`evaluation/aider_bench`](./aider_bench/)

### Web Browsing

- WebArena: [`evaluation/webarena`](./webarena/)
- MiniWob++: [`evaluation/miniwob`](./miniwob/)

### Misc. Assistance

- GAIA: [`evaluation/gaia`](./gaia)
- GPQA: [`evaluation/gpqa`](./gpqa)
- AgentBench: [`evaluation/agent_bench`](./agent_bench)
- MINT: [`evaluation/mint`](./mint)
- Entity deduction Arena (EDA): [`evaluation/EDA`](./EDA)
- ProofWriter: [`evaluation/logic_reasoning`](./logic_reasoning)

## Before everything begins: Setup Environment and LLM Configuration

Please follow instruction [here](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to setup your local development environment and LLM.

OpenHands in development mode uses `config.toml` to keep track of most configurations.

Here's an example configuration file you can use to define and use multiple LLMs:

```toml
[llm]
# IMPORTANT: add your API key here, and set the model to the one you want to evaluate
model = "gpt-4o-2024-05-13"
api_key = "sk-XXX"

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

Check [this huggingface space](https://huggingface.co/spaces/OpenHands/evaluation) for visualization of existing experimental results.

### Upload your results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results to our hosted huggingface repo via PR following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
