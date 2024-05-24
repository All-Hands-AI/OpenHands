# GAIA Evaluation

This folder contains evaluation harness for evaluating agents on
the [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md)
for how to set this up.

## Start the evaluation

Following is the basic command to start the evaluation. Here we are only evaluating the `os-std` for now.

You can update the arguments in the script `evaluation/agent_bench/scripts/run_infer.sh`, such as `--max-iterations`, `--eval-num-workers` and so on.

```bash
 evaluation/agent_bench/scripts/run_infer.sh eval_gpt35_turbo CodeActAgent 1
```
