# VisualWebArena Evaluation with OpenHands Browsing Agents

This folder contains evaluation for [VisualWebArena](https://github.com/web-arena-x/visualwebarena) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on realistic web browsing tasks.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Setup VisualWebArena Environment

VisualWebArena requires you to set up websites containing pre-populated content that is accessible via URL to the machine running the OpenHands agents.
Follow [this document](https://github.com/web-arena-x/visualwebarena/blob/main/environment_docker/README.md) to set up your own VisualWebArena environment through local servers or AWS EC2 instances.
Take note of the base URL (`$VISUALWEBARENA_BASE_URL`) of the machine where the environment is installed.

## Test if your environment works

Access with browser the above VisualWebArena website URLs and see if they load correctly.
If you cannot access the website, make sure the firewall allows public access of the aforementioned ports on your server
Check the network security policy if you are using an AWS machine.
Follow the VisualWebArena environment setup guide carefully, and make sure the URL fields are populated with the correct base URL of your server.

## Run Evaluation

```bash
export VISUALWEBARENA_BASE_URL=<YOUR_SERVER_URL_HERE>
export OPENAI_API_KEY="yourkey" # this OpenAI API key is required for some visualWebArena validators that utilize LLMs
export OPENAI_BASE_URL="https://api.openai.com/v1/" # base URL for OpenAI model used for VisualWebArena evaluation
bash evaluation/benchmarks/visualwebarena/scripts/run_infer.sh llm.claude HEAD VisualBrowsingAgent
```

Results will be in `evaluation/evaluation_outputs/outputs/visualwebarena/`

To calculate the success rate, run:

```sh
poetry run python evaluation/benchmarks/visualwebarena/get_success_rate.py evaluation/evaluation_outputs/outputs/visualwebarena/SOME_AGENT/EXP_NAME/output.jsonl
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).

## VisualBrowsingAgent V1.0 result

Tested on VisualBrowsingAgent V1.0

VisualWebArena, 910 tasks (high cost, single run due to fixed task), max step 15. Resolve rates are:

- GPT4o: 26.15%
- Claude-3.5 Sonnet: 25.27%
