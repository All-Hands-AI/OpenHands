# SWE-Bench Evaluation with OpenHands SWE-Bench Docker Image

This folder contains the evaluation harness that we built on top of the original TestGenEval benchmark ([paper](https://arxiv.org/abs/2410.00752)).

## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local development environment and LLM.

### Run Inference

```bash
./evaluation/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]


### Specify a subset of tasks to run infer

If you would like to specify a list of tasks you'd like to benchmark on, you could
create a `config.toml` under `./evaluation/swe_bench/` folder, and put a list
attribute named `selected_ids`, e.g.

```toml
selected_ids = ['sphinx-doc__sphinx-8721', 'sympy__sympy-14774', 'scikit-learn__scikit-learn-10508']
```

Then only these tasks (rows whose `instance_id` is in the above list) will be evaluated.
In this case, `eval_limit` option applies to tasks that are in the `selected_ids` list.

After running the inference, you will obtain a `output.jsonl` (by default it will be saved to `evaluation/evaluation_outputs`).

## Evaluate Generated Tests

### Run evaluation

With `output.jsonl` file, you can run `eval_infer.sh` to evaluate generated patches, and produce a fine-grained report.

```bash
./evaluation/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL [instance_id] [dataset_name] [split] [num_workers] [skip_mutation]

# Example
./evaluation/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/swe_bench/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/output.jsonl
```

The script now accepts optional arguments:
- `instance_id`: Specify a single instance to evaluate (optional)
- `dataset_name`: The name of the dataset to use (default: `"kjain14/testgenevallite"`)
- `split`: The split of the dataset to use (default: `"test"`)
- `num_workers`: The number of workers to use when running docker (default: 1)
- `skip_mutation`: Whether to skip mutation testing (enter true if so)

For example, to evaluate a specific instance with a custom dataset and split:

```bash
./evaluation/swe_bench/scripts/eval_infer.sh $YOUR_OUTPUT_JSONL instance_123 kjain14/testgenevallite
```

The final results will be saved to `evaluation/evaluation_outputs/outputs/testgeneval/CodeActAgent/gpt-4-1106-preview_maxiter_50_N_v1.0/` with the `output.testgeneval.jsonl` containing the metrics.

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).
