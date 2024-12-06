# EDA Evaluation

This folder contains evaluation harness for evaluating agents on the Entity-deduction-Arena Benchmark, from the paper [Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games](https://arxiv.org/abs/2310.01468), presented in ACL 2024 main conference.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Start the evaluation

```bash
export OPENAI_API_KEY="sk-XXX"; # This is required for evaluation (to simulate another party of conversation)
./evaluation/benchmarks/EDA/scripts/run_infer.sh [model_config] [git-version] [agent] [dataset] [eval_limit]
```

where `model_config` is mandatory, while `git-version`, `agent`, `dataset` and `eval_limit` are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

- `dataset`: There are two tasks in this evaluation. Specify `dataset` to test on either `things` or `celebs` task.

- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By default it infers all instances.

For example,

```bash
./evaluation/benchmarks/EDA/scripts/run_infer.sh eval_gpt4o_2024_05_13 0.6.2 CodeActAgent things
```

## Reference

```bibtex
@inproceedings{zhang2023entity,
  title={Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games},
  author={Zhang, Yizhe and Lu, Jiarui and Jaitly, Navdeep},
  journal={ACL},
  year={2024}
}
```
