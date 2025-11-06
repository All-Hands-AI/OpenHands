# PaperBench Evaluation with OpenHands

This folder contains the evaluation harness that we built on top of the original [Paper Bench](https://github.com/openai/frontier-evals/tree/main/project/paperbench) ([paper](https://arxiv.org/abs/2504.01848)).

The evaluation consists of three steps:

1. Environment setup: [install python environment](../../README.md#development-environment), [configure LLM config](../../README.md#configure-openhands-and-your-llm), [launch services](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/SETUP.md).
2. [Run Inference](#run-inference-on-paper-bench-tasks): Run all tasks and get submissions.
3. [Run Evaluation](#run-evaluation-on-task-submissions): Run judge on submissions.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.
Install Dependencies for Paper Bench:
```bash
uv pip install "git+https://github.com/leandermaben/frontier-evals.git#subdirectory=project/paperbench"
```

## Run Inference on Paper Bench Tasks

When the `run_infer.sh` script is started, it will automatically pull all task images. Every task image will be used to create an OpenHands runtime image where the agent will operate on.

```bash
./evaluation/benchmarks/the_agent_company/scripts/run_infer.sh \
  --agent-llm-config <agent-llm-config, default to 'agent'>  \
  --outputs-path <outputs-path, default to outputs> \
  --start-percentile <integer from 0 to 99, default to 0> \
  --end-percentile <integer from 1 to 100, default to 100>


# Example
./evaluation/benchmarks/the_agent_company/scripts/run_infer.sh \
  --agent-llm-config claude-3-5-sonnet-20240620 \
  --outputs-path outputs \
  --start-percentile 10 \
  --end-percentile 20
```

##Run Evaluation on Paper Bench Tasks

``bash
./evaluation/benchmarks/the_agent_company/scripts/run_eval.sh \
  --submissions-path <submissions-path, default to 'output/submissions'>  \


# Example
./evaluation/benchmarks/the_agent_company/scripts/run_eval.sh \
  --submissions-path output/submissions
```

- `output-submissions`- Path to dir where inference script save submissions for tasks
