# ScienceAgentBench Evaluation with OpenHands

This folder contains the evaluation harness for [ScienceAgentBench](https://osu-nlp-group.github.io/ScienceAgentBench/) (paper: <https://arxiv.org/abs/2410.05080>).

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Setup ScienceAgentBench

To prevent benchmark data contamination, we only provide the annotation sheet on [Huggingface](https://huggingface.co/datasets/osunlp/ScienceAgentBench), which includes all necessary *inputs* to run an agent.

## Run Inference on ScienceAgentBench

```bash
./evaluation/benchmarks/scienceagentbench/scripts/run_infer.sh [model_config] [git-version] [use_knowledge] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]

# Example
./evaluation/benchmarks/scienceagentbench/scripts/run_infer.sh llm.eval_gpt4o 0.9.3
```

where `model_config` is mandatory, and the rest are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.
- `use_knowledge`, e.g. `true`, specifies whether allowing the agent to use expert-provided knowledge as additional input or not. By default, it is set to `false`.
- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.
- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By
default, the script evaluates the entire SWE-bench_Lite test set (300 issues). Note:
in order to use `eval_limit`, you must also set `agent`.
- `max_iter`, e.g. `20`, is the maximum number of iterations for the agent to run. By
default, it is set to 30.
- `num_workers`, e.g. `3`, is the number of parallel workers to run the evaluation. By
default, it is set to 1.

## Evaluate Generated Programs

### Extract Necessary Information from OpenHands Log

After the inference is completed, you may use the following command to extract necessary information from the output log for evaluation:

```bash
python post_proc.py [log_fname]
```

- `log_fname`, e.g. `evaluation/.../output.jsonl`, is the automatically saved trajectory log of an OpenHands agent.

Output will be write to e.g. `evaluation/.../output.converted.jsonl`

### Run evaluation

Please follow the steps [here](https://github.com/OSU-NLP-Group/ScienceAgentBench/tree/main?tab=readme-ov-file#evaluation-of-generated-code) to evaluate the generated programs.
