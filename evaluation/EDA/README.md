# EDA Evaluation

This folder contains evaluation harness for evaluating agents on the Entity-deduction-Arena Benchmark, from the paper [Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games](https://arxiv.org/abs/2310.01468), presented in ACL 2024 main conference.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation


```bash
export OPENAI_API_KEY="sk-XXX"; # This is required for evaluation (to simulate another party of conversation)
./evaluation/EDA/scripts/run_infer.sh [model_config] [agent] [dataset] [eval_limit]
```

where `model_config` is mandatory, while `agent`, `dataset` and `eval_limit` are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

- `dataset`: There are two tasks in this evaluation. Specify `dataset` to test on either `things` or `celebs` task.

- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By default it infers all instances.

Let's say you'd like to run 10 instances using `eval_gpt4_1106_eval_gpt4o_2024_05_13preview` and CodeActAgent,
then your command would be:

```bash
./evaluation/EDA/scripts/run_infer.sh eval_gpt4o_2024_05_13 CodeActAgent things
```

## Reference
```
@inproceedings{zhang2023entity,
  title={Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games},
  author={Zhang, Yizhe and Lu, Jiarui and Jaitly, Navdeep},
  journal={ACL},
  year={2024}
}
```
