# The Agent Company Evaluation with OpenHands

This folder contains the evaluation harness that we built on top of the original [The Agent Company](https://github.com/TheAgentCompany/TheAgentCompany/tree/main/evaluation) ([paper](https://arxiv.org/abs/2412.14161)).

The evaluation consists of three steps:

1. Environment setup: [install python environment](../../README.md#development-environment), [configure LLM config](../../README.md#configure-openhands-and-your-llm), [launch services](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/SETUP.md).
2. [Run Evaluation](#run-inference-on-the-agent-company-tasks): Run all tasks and get the evaluation results.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on The Agent Company Tasks

When the `run_infer.sh` script is started, it will automatically pull all task images. Every task image will be used to create an OpenHands runtime image where the agent will operate on.

```bash
./evaluation/benchmarks/the_agent_company/scripts/run_infer.sh \
  --agent-llm-config <agent-llm-config, default to 'agent'>  \
  --env-llm-config <env-llm-config, default to 'env'> \
  --outputs-path <outputs-path, default to outputs> \
  --server-hostname <server-hostname, default to localhost> \
  --version <version, default to 1.0.0> \
  --start-percentile <integer from 0 to 99, default to 0> \
  --end-percentile <integer from 1 to 100, default to 100>


# Example
./evaluation/benchmarks/the_agent_company/scripts/run_infer.sh \
  --agent-llm-config claude-3-5-sonnet-20240620 \
  --env-llm-config claude-3-5-sonnet-20240620 \
  --outputs-path outputs \
  --server-hostname localhost \
  --version 1.0.0 \
  --start-percentile 10 \
  --end-percentile 20
```

- `agent-llm-config`: the config name for the agent LLM. This should match the config name in config.toml. This is the LLM used by the agent (e.g. CodeActAgent).
- `env-llm-config`: the config name for the environment LLM. This should match the config name in config.toml. This is used by the chat bots (NPCs) and LLM-based evaluators.
- `outputs-path`: the path to save trajectories and evaluation results.
- `server-hostname`: the hostname of the server that hosts all the web services. It could be localhost if you are running the evaluation and services on the same machine. If the services are hosted on a remote machine, you must use the hostname of the remote machine rather than IP address.
- `version`: the version of the task images to use. Currently, the only supported version is 1.0.0.
- `start-percentile`: the start percentile of the task split, must be an integer between 0 to 99.
- `end-percentile`: the end percentile of the task split, must be an integer between 1 to 100 and larger than start-percentile.

The script is idempotent. If you run it again, it will resume from the last checkpoint. It would usually take 2 days to finish evaluation if you run the whole task set.
To speed up evaluation, you can use `start-percentile` and `end-percentile` to split the tasks for higher parallelism,
provided concurrent runs are **targeting different servers**.

Note: the script will automatically skip a task if it encounters an error. This usually happens when the OpenHands runtime dies due to some unexpected errors. This means even if the script finishes, it might not have evaluated all tasks. You can manually resume the evaluation by running the script again.
