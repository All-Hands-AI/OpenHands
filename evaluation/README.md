# Evaluation

This folder contains code and resources to run experiments and evaluations.

## For Benchmark Users

### Setup

Before starting evaluation, follow the instructions [here](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to setup your local development environment and LLM.

Once you are done with setup, you can follow the benchmark-specific instructions in each subdirectory of the [evaluation directory](#supported-benchmarks).
Generally these will involve running `run_infer.py` to perform inference with the agents.

### Implementing and Evaluating an Agent

To add an agent to OpenHands, you will need to implement it in the [agenthub directory](https://github.com/All-Hands-AI/OpenHands/tree/main/openhands/agenthub). There is a README there with more information.

To evaluate an agent, you can provide the agent's name to the `run_infer.py` program.

### Evaluating Different LLMs

OpenHands in development mode uses `config.toml` to keep track of most configuration.
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

## Supported Benchmarks

The OpenHands evaluation harness supports a wide variety of benchmarks across [software engineering](#software-engineering), [web browsing](#web-browsing), [miscellaneous assistance](#misc-assistance), and [real-world](#real-world) tasks.

### Software Engineering

- SWE-Bench: [`evaluation/benchmarks/swe_bench`](./benchmarks/swe_bench)
- HumanEvalFix: [`evaluation/benchmarks/humanevalfix`](./benchmarks/humanevalfix)
- BIRD: [`evaluation/benchmarks/bird`](./benchmarks/bird)
- BioCoder: [`evaluation/benchmarks/ml_bench`](./benchmarks/ml_bench)
- ML-Bench: [`evaluation/benchmarks/ml_bench`](./benchmarks/ml_bench)
- APIBench: [`evaluation/benchmarks/gorilla`](./benchmarks/gorilla/)
- ToolQA: [`evaluation/benchmarks/toolqa`](./benchmarks/toolqa/)
- AiderBench: [`evaluation/benchmarks/aider_bench`](./benchmarks/aider_bench/)
- Commit0: [`evaluation/benchmarks/commit0_bench`](./benchmarks/commit0_bench/)
- DiscoveryBench: [`evaluation/benchmarks/discoverybench`](./benchmarks/discoverybench/)

### Web Browsing

- WebArena: [`evaluation/benchmarks/webarena`](./benchmarks/webarena/)
- MiniWob++: [`evaluation/benchmarks/miniwob`](./benchmarks/miniwob/)
- Browsing Delegation: [`evaluation/benchmarks/browsing_delegation`](./benchmarks/browsing_delegation/)

### Misc. Assistance

- GAIA: [`evaluation/benchmarks/gaia`](./benchmarks/gaia)
- GPQA: [`evaluation/benchmarks/gpqa`](./benchmarks/gpqa)
- AgentBench: [`evaluation/benchmarks/agent_bench`](./benchmarks/agent_bench)
- MINT: [`evaluation/benchmarks/mint`](./benchmarks/mint)
- Entity deduction Arena (EDA): [`evaluation/benchmarks/EDA`](./benchmarks/EDA)
- ProofWriter: [`evaluation/benchmarks/logic_reasoning`](./benchmarks/logic_reasoning)
- ScienceAgentBench: [`evaluation/benchmarks/scienceagentbench`](./benchmarks/scienceagentbench)

### Real World

- TheAgentCompany: [`evaluation/benchmarks/the_agent_company`](./benchmarks/the_agent_company)

## Result Visualization

Check [this huggingface space](https://huggingface.co/spaces/OpenHands/evaluation) for visualization of existing experimental results.

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results to our hosted huggingface repo via PR following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).

## For Benchmark Developers

To learn more about how to integrate your benchmark into OpenHands, check out [tutorial here](https://docs.all-hands.dev/modules/usage/how-to/evaluation-harness). Briefly,

- Each subfolder contains a specific benchmark or experiment. For example, [`evaluation/benchmarks/swe_bench`](./benchmarks/swe_bench) should contain
all the preprocessing/evaluation/analysis scripts.
- Raw data and experimental records should not be stored within this repo.
- For model outputs, they should be stored at [this huggingface space](https://huggingface.co/spaces/OpenHands/evaluation) for visualization.
- Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.
