# DiscoveryBench with OpenHands

[DiscoveryBench](https://github.com/allenai/discoverybench/) [(Paper)](https://arxiv.org/abs/2407.01725v1) contains 264 tasks collected across 6 diverse domains, such as biology, economics, and sociology. It incorporates discovery workflows from published papers to approximate the real-world challenges faced by researchers.

<p align="center">
  <a href="[https://github.com/allenai/discoverybench](https://github.com/allenai/discoverybench)">
    <img src="https://raw.githubusercontent.com/allenai/discoverybench/refs/heads/main/assets/discoverybench-openhands-teaser.png" width="100%" alt="DiscoveryBench Background" />
  </a>
</p>


## Setup Environment and LLM Configuration

1. Please follow instructions mentioned [here](https://github.com/openlocus/OpenHands/blob/discoverybench-openhands-integration/evaluation/README.md#setup) to setup OpenHands development environment and LLMs locally

2. Execute the bash script to start DiscoveryBench Evaluation

```
./evaluation/benchmarks/discoverybench/scripts/run_infer.sh [YOUR MODEL CONFIG]
```
Replace `[YOUR MODEL CONFIG]` with any model the model that you have set up in `config.toml`


## Run Inference on DiscoveryBench Instances

When the `run_infer.sh` script is started, it will automatically pull the latest DiscoveryBench instances & set up the agent environment. The OpenHands agent is invoked to process the task within this environment, producing a hypothesis. We then evaluate it against the “gold” hypothesis provided by DiscoveryBench. The evaluation result, along with the agent chat history is logged to `output.jsonl` under `evaluation_outputs`.


```
./evaluation/benchmarks/discoverybench/scripts/run_infer.sh [MODEL_CONFIG] [GIT_COMMIT] [AGENT] [EVAL_LIMIT] [NUM_WORKERS]
```

- `MODEL_CONFIG`: Name of the model you want to evaluate with
- `GIT_COMMIT`: This should be the git commit hash or release tag for OpenHands, e.g., HEAD or a specific tag like 0.6.2.
- `AGENT`: Use CoderActAgent, right now it only supports that.
- `EVAL_LIMIT`: Number of samples to evaluate.
- `NUM_WORKERS`: Number of workers to parallelize the evaluation process.
