# WebArena Evaluation with OpenDevin Browsing Agents

This folder contains evaluation for [WebArena](https://github.com/web-arena-x/webarena) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on realistic web browsing tasks.

## Setup OpenDevin Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
sandbox_container_image = "ghcr.io/opendevin/sandbox:latest"
sandbox_type = "ssh"
ssh_hostname = "localhost"
sandbox_timeout = 120

# TODO: Change these to the model you want to evaluate
[eval_gpt4_1106_preview]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[eval_some_openai_compatible_model]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

## Setup WebArena Environment
WebArena requires you to set up websites containing pre-populated content that is accessible via URL to the machine running the OpenDevin agents.
Follow [this document](https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md) to set up your own WebArena environment through local servers or AWS EC2 instances.
Take note of the base URL of the machine where the environment is installed.

## Setup Environment Variables of WebArena Websites

Create a script `webarena_env.sh` under `evaluation/webarena/scripts` with the following:

```bash
export BASE_URL=<YOUR_SERVER_URL_HERE>
export SHOPPING="$BASE_URL:7770/"
export SHOPPING_ADMIN="$BASE_URL:7780/admin"
export REDDIT="$BASE_URL:9999"
export GITLAB="$BASE_URL:8023"
export WIKIPEDIA="$BASE_URL:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
export MAP="$BASE_URL:3000"
export HOMEPAGE="$BASE_URL:4399"
export OPENAI_API_KEY="yourkey" # this key is required for some WebArena validators that utilize LLMs
```

## Test if your environment works

Access with browser the above WebArena website URLs and see if they load correctly.
If you cannot access the website, make sure the firewall allows public access of the aforementioned ports on your server
Check the network security policy if you are using an AWS machine.
Follow the WebArena environment setup guide carefully, and make sure the URL fields are populated with the correct base URL of your server.

## Run Evaluation

```sh
bash evaluation/webarena/scripts/run_infer.sh
```

Results will be in `evaluation/evaluation_outputs/outputs/webarena/`

To calculate the success rate, run:

```sh
poetry run python evaluation/webarena/get_success_rate.py evaluation/evaluation_outputs/outputs/webarena/SOME_AGENT/EXP_NAME/output.jsonl
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).


## BrowsingAgent V1.0 result

Tested on BrowsingAgent V1.0

WebArena, 812 tasks (high cost, single run due to fixed task), max step 15

- GPT4o: 0.1478
- GPT3.5: 0.0517
