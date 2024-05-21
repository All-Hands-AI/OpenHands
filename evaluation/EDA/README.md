# EDA Evaluation

This folder contains evaluation harness for evaluating agents on the Entity-deduction-Arena Benchmark, from the paper [Probing the Multi-turn Planning Capabilities of LLMs via 20 Question Games](https://arxiv.org/abs/2310.01468), presented in ACL 2024 main conference.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation
Following is the basic command to start the evaluation. Here we are only evaluating the first instance of the validation set for the 2023_level1 split.


You can remove the `--eval-n-limit 1` argument to evaluate all instances in the validation set. Or change `--data-split` `--data-split` to test other splits.
```bash
python ./evaluation/gaia/run_infer.py \
--level 2023_level1 \
--data-split validation \
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
