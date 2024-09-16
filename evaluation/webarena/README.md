# WebArena Evaluation with OpenHands Browsing Agents

This folder contains evaluation for [WebArena](https://github.com/web-arena-x/webarena) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on realistic web browsing tasks.

## Setup Environment and LLM Configuration

Please follow instruction [here](../README.md#setup) to setup your local development environment and LLM.

## Setup WebArena Environment

WebArena requires you to set up websites containing pre-populated content that is accessible via URL to the machine running the OpenHands agents.
Follow [this document](https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md) to set up your own WebArena environment through local servers or AWS EC2 instances.
Take note of the base URL (`$WEBARENA_BASE_URL`) of the machine where the environment is installed.

## Test if your environment works

Access with browser the above WebArena website URLs and see if they load correctly.
If you cannot access the website, make sure the firewall allows public access of the aforementioned ports on your server
Check the network security policy if you are using an AWS machine.
Follow the WebArena environment setup guide carefully, and make sure the URL fields are populated with the correct base URL of your server.

## Run Evaluation

```bash
export WEBARENA_BASE_URL=<YOUR_SERVER_URL_HERE>
export OPENAI_API_KEY="yourkey" # this key is required for some WebArena validators that utilize LLMs
bash evaluation/webarena/scripts/run_infer.sh
```

Results will be in `evaluation/evaluation_outputs/outputs/webarena/`

To calculate the success rate, run:

```sh
poetry run python evaluation/webarena/get_success_rate.py evaluation/evaluation_outputs/outputs/webarena/SOME_AGENT/EXP_NAME/output.jsonl
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).

## BrowsingAgent V1.0 result

Tested on BrowsingAgent V1.0

WebArena, 812 tasks (high cost, single run due to fixed task), max step 15

- GPT4o: 0.1478
- GPT3.5: 0.0517
