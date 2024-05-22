# Logic Reasoning Evaluation

This folder contains evaluation harness for evaluating agents on the logic reasoning benchmark [ProntoQA](https://github.com/asaparov/prontoqa) and [ProofWriter](https://allenai.org/data/proofwriter).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## Start the evaluation
Following is the basic command to start the evaluation. Here we are only evaluating the first example of the validation set for the ProntoQA.


You can remove the `--eval-n-limit 1` argument to evaluate all instances in the validation set. `--data-split` only support `validation` right now.
```bash
python ./evaluation/logic_reasoning/run_infer.py \
--dataset ProntoQA \
--data-split validation \
--eval-n-limit 1
```
