# 🛰️ DiscoveryBench with 🙌 OpenHands

TODO: This is sample description, need to update it before upstream PR.
DiscoveryBench is designed to systematically assess current model capabilities in data-driven discovery tasks and provide a useful resource for improving them. Each DiscoveryBench task consists of a goal and dataset(s). Solving the task requires both statistical analysis and semantic reasoning. A faceted evaluation allows open-ended final answers to be rigorously evaluated.


## ⚙️ Setup Environment and LLM Configuration

1. Please follow instructions mentioned [here](https://github.com/openlocus/OpenHands/blob/discoverybench-openhands-integration/evaluation/README.md#setup) to setup OpenHands development environment and LLMs locally

2. Execute the bash script to start DiscoveryBench Evaluation

```
./evaluation/discoverybench/scripts/run_infer.sh [YOUR MODEL CONFIG]
```
Replace `[YOUR MODEL CONFIG]` with any model the model that you have set up in `config.toml`

3. Other configurations
```
./evaluation/discoverybench/scripts/run_infer.sh [MODEL_CONFIG] [GIT_COMMIT] [AGENT] [EVAL_LIMIT] [NUM_WORKERS]
```

- `MODEL_CONFIG`: Name of the model you want to evaluate with
- `GIT_COMMIT`: This should be the git commit hash or release tag for OpenHands, e.g., HEAD or a specific tag like 0.6.2.
- `AGENT`: For the agent, it appears you're using CodeActAgent. Replace [AGENT] with CodeActAgent.
- `EVAL_LIMIT`: This should be the number of samples to evaluate, e.g., num_samples_eval.
- `NUM_WORKERS`: This would be the number of workers to parallelize the evaluation process.

## ✨ Overview

- A DiscoveryBench instance is a scientific discovery task in natural language.
- In each iteration, OpenHands' agent try to solve the problem provided to it using python.
- After the iteration is complete, we evaluate the agent result based on our gold hypothesis.
- The evaluation result, along with the agent chat history is logged to `output.jsonl` under `evaluation_outputs`
