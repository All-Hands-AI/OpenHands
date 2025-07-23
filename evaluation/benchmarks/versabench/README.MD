# VersaBench: A Diverse Benchmark for Software Engineering

This folder provides scripts to run all benchmarks contained inside VersaBench with a single entry point.

## Setup Environment and LLM Configuration

Please follow the instructions [here](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/README.md#setup) to set up your local development environment and LLM.

## Running `install.sh`

Run the following to download split folders and other dependencies:

```bash
./install.sh
```

## Tokens and Configs

Ensure that:
- You have a valid `config.yaml` in the `lca_build_repair` directory. Including the organization token provided by the LCA team.
- You have set up a Tavily API key.

## Running Inference

To run inference:

```bash
poetry run python ./evaluation/benchmarks/versabench/run_infer.py --split name_of_split --llm name_of_llm
```

### Example:

```bash
poetry run python ./evaluation/benchmarks/versabench/run_infer.py --split 20250611 --llm llm.eval-proxy-claude-sonnet-4-20250514
```

## Running Evaluation

You can run

```bash
poetry run python ./evaluation/benchmarks/versabench/eval_infer.py \
  --swe [path_to_output.jsonl] \
  --swt [path_to_output.jsonl] \
  --gaia [path_to_output.jsonl] \
  --lca-ci [path_to_output.jsonl] \
  --multi-swe [path_to_output.jsonl] \
  --commit0 [path_to_output.jsonl] \
  --the-agent-comapny [path_to_output-folder]
```

For Multimodal, please run evaluation script independently.
