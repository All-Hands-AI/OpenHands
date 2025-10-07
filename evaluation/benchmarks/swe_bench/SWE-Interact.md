# SWE-Interact Benchmark

This document explains how to use the [Interactive SWE-Bench](https://arxiv.org/abs/2502.13069) benchmark scripts for running and evaluating interactive software engineering tasks.

## Setting things up
After following the [README](./README.md) to set up the environment, you would need to additionally add LLM configurations for simulated human users. In the original [paper](https://arxiv.org/abs/2502.13069), we use gpt-4o as the simulated human user. You can add the following to your `config.toml` file:

```toml
[llm.fake_user]
model="litellm_proxy/gpt-4o-2024-08-06"
api_key="<your-api-key>"
temperature = 0.0
base_url = "https://llm-proxy.eval.all-hands.dev"
```

## Running the Benchmark

The main script for running the benchmark is `run_infer_interact.sh`. Here's how to use it:

```bash
bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh <model_config> <commit_hash> <agent> <eval_limit> <max_iter> <num_workers> <split>
```

### Parameters:

- `model_config`: Path to the LLM configuration file (e.g., `llm.claude-3-7-sonnet`)
- `commit_hash`: Git commit hash to use (e.g., `HEAD`)
- `agent`: The agent class to use (e.g., `CodeActAgent`)
- `eval_limit`: Number of examples to evaluate (e.g., `500`)
- `max_iter`: Maximum number of iterations per task (e.g., `100`)
- `num_workers`: Number of parallel workers (e.g., `1`)
- `split`: Dataset split to use (e.g., `test`)

### Example:

```bash
bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh llm.claude-3-7-sonnet HEAD CodeActAgent 500 100 1 test
```

### Additional Environment Variables:

You can customize the behavior using these environment variables:

- `RUN_WITH_BROWSING`: Enable/disable web browsing (default: false)
- `USE_HINT_TEXT`: Enable/disable hint text (default: false)
- `EVAL_CONDENSER`: Specify a condenser configuration
- `EXP_NAME`: Add a custom experiment name to the output
- `N_RUNS`: Number of runs to perform (default: 1)
- `SKIP_RUNS`: Comma-separated list of run numbers to skip

## Evaluating Results

After running the benchmark, you can evaluate the results using `eval_infer.sh`:

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh <output_file> <instance_id> <dataset> <split>
```

### Parameters:

- `output_file`: Path to the output JSONL file
- `instance_id`: The specific instance ID to evaluate
- `dataset`: Dataset name (e.g., `cmu-lti/interactive-swe`)
- `split`: Dataset split (e.g., `test`)

### Example:

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/cmu-lti__interactive-swe-test/CodeActAgent/claude-3-7-sonnet-20250219_maxiter_100_N_v0.39.0-no-hint-run_1/output.jsonl sphinx-doc__sphinx-8721 cmu-lti/interactive-swe test
```

## Output Structure

The benchmark outputs are stored in the `evaluation/evaluation_outputs/outputs/` directory with the following structure:

```
evaluation/evaluation_outputs/outputs/
└── cmu-lti__interactive-swe-{split}/
    └── {agent}/
        └── {model}-{date}_maxiter_{max_iter}_N_{version}-{options}-run_{run_number}/
            └── output.jsonl
```

Where:
- `{split}` is the dataset split (e.g., test)
- `{agent}` is the agent class name
- `{model}` is the model name
- `{date}` is the run date
- `{max_iter}` is the maximum iterations
- `{version}` is the OpenHands version
- `{options}` includes any additional options (e.g., no-hint, with-browsing)
- `{run_number}` is the run number
