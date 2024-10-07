# AiderBench Evaluation

This folder contains evaluation harness for evaluating agents on the
[Aider Editing Benchmark](https://github.com/paul-gauthier/aider/blob/main/benchmark/README.md).
This will allow us to develop better editing approach without running the full
SWE-bench. The benchmark uses the
[RajMaheshwari/Exercism-Python](https://huggingface.co/datasets/RajMaheshwari/Exercism-Python)
Hugging Face dataset based on the
[Exercism python coding exercises](https://github.com/exercism/python).

## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local
development environment and LLM.

## Start the evaluation

```bash
./evaluation/aider_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [eval-num-workers] [eval_ids]
```

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for
    your LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version
    you would like to evaluate. It could also be a release tag like `0.9.0`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks,
    defaulting to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit`
    instances. By default, the script evaluates the entire Exercism test set
    (133 issues). Note: in order to use `eval_limit`, you must also set `agent`.
- `eval-num-workers`: the number of workers to use for evaluation. Default: `1`.
- `eval_ids`, e.g. `"1,3,10"`, limits the evaluation to instances with the
    given IDs (comma separated).

There are also following optional environment variables you can set:

```bash
export USE_UNIT_TESTS=true # if you want to allow the Agent to verify correctness using unittests. Default to false.
export SKIP_NUM=12 # skip the first 12 instances from the dataset
```

Following is the basic command to start the evaluation.

You can update the arguments in the script
`evaluation/aider_bench/scripts/run_infer.sh`, such as `--max-iterations`,
`--eval-num-workers` and so on:

- `--agent-cls`, the agent to use. For example, `CodeActAgent`.
- `--llm-config`: the LLM configuration to use. For example, `eval_gpt4_1106_preview`.
- `--max-iterations`: the max allowed number of iterations to run the evaluation. Default: `30`.
- `--eval-num-workers`: the number of workers to use for evaluation. Default: `1`.
- `--eval-n-limit`: the number of examples to evaluate. For example, `100`.
- `--eval-ids`: the IDs of the examples to evaluate (comma separated). For example, `"1,3,10"`.

```bash
./evaluation/aider_bench/scripts/run_infer.sh eval_gpt35_turbo HEAD CodeActAgent 100 1 "1,3,10"
```

## Summarize Results

```bash
poetry run python ./evaluation/aider_bench/scripts/summarize_results.py [path_to_output_jsonl_file]
```

Full example:

```bash
poetry run python ./evaluation/aider_bench/scripts/summarize_results.py evaluation/evaluation_outputs/outputs/AiderBench/CodeActAgent/claude-3-5-sonnet@20240620_maxiter_30_N_v1.9/output.jsonl
```

This will list the instances that passed and the instances that failed. For each
instance, the corresponding set of test cases (which can vary for each instance)
are run on the file edited by the agent. We consider an instance to be passed
only if ALL test cases are passed. Sometimes even a single failed test case will
cause the entire instance to be marked as failed.

You can inspect the `test_results` field in the `output.jsonl` file to find the exact
outcome of the tests. If there are no syntax or indentation errors, you can
expect to see something like "`..F...EF..`", where "`.`" means the test case
passed, "`E`" means there was an error while executing the test case and "`F`"
means some assertion failed and some returned output was not as expected.
