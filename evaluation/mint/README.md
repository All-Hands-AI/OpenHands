# MINT Benchmark

This folder contains the evaluation harness for the [MINT benchmark](https://arxiv.org/abs/2309.10691) on LLMs' ability to solve tasks with multi-turn interactions.

## Configure OpenDevin and LM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation

```
bash ./evaluation/mint/run_infer.sh math 2
```
