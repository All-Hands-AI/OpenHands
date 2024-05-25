# EDA Evaluation

This folder contains evaluation harness for evaluating agents on the Entity-deduction-Arena Benchmark, from the paper [Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games](https://arxiv.org/abs/2310.01468), presented in ACL 2024 main conference.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation
There are two tasks in this evaluation. Specify `--dataset` to test on either `things` or `celebs` task.

You can remove the `--eval-n-limit 1` argument to evaluate all instances in the validation set. Alternatively, you can change `--data-split` to test other splits (see https://huggingface.co/docs/datasets/main/en/loading#slice-splits for available options).

The `--max-iterations` should be set to 20 to be comparable to other LLMs in the [leaderboard](https://github.com/apple/ml-entity-deduction-arena?tab=readme-ov-file#highlights).

```bash
pip install retry

python ./evaluation/EDA/run_infer.py \
--dataset things \
--data-split test \
--max-iterations 20 \
--OPENAI_API_KEY sk-xxx \
--eval-n-limit 1
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
