# WebArena Evaluation with OpenHands Browsing Agents

This folder contains evaluation for [WebArena](https://github.com/web-arena-x/webarena) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on realistic web browsing tasks.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

Make sure to install the evaluation dependencies:

```bash
poetry install --with evaluation
```

## Setup WebArena Environment

WebArena requires access to websites containing pre-populated content. You can either:

1. **Use an existing WebArena environment** (recommended for evaluation): Set the `WEBARENA_BASE_URL` environment variable to point to an existing WebArena server.

2. **Set up your own environment**: Follow [this document](https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md) to set up your own WebArena environment through local servers or AWS EC2 instances.

The WebArena evaluation package is already installed with the evaluation dependencies, so you don't need to clone the WebArena repository separately.

## Test if your environment works

Access with browser the above WebArena website URLs and see if they load correctly.
If you cannot access the website, make sure the firewall allows public access of the aforementioned ports on your server
Check the network security policy if you are using an AWS machine.
Follow the WebArena environment setup guide carefully, and make sure the URL fields are populated with the correct base URL of your server.

## Run Evaluation

### Step 1: Run Inference
Before running, you must provide an LLM config in a local config.toml and pass its name to run_infer.sh:

1) Create config.toml in the repo root (this file is gitignored):

```toml
[llm.eval_openai]
model = "gpt-4o"
api_key = "sk-..."   # Your OpenAI API key
```

2) Ensure Docker is installed and running (the first run will build a browser-enabled runtime image).


```bash
export WEBARENA_BASE_URL=<YOUR_SERVER_URL_HERE>
export OPENAI_API_KEY="yourkey" # this key is required for some WebArena validators that utilize LLMs
# args: MODEL_CONFIG  COMMIT_HASH  AGENT  EVAL_LIMIT  NUM_WORKERS
bash evaluation/benchmarks/webarena/scripts/run_infer.sh llm.eval_openai HEAD BrowsingAgent 3 1
```

Results will be in `evaluation/evaluation_outputs/outputs/webarena/`

### Step 2: Evaluate Results

To evaluate the results and calculate success rate using the official WebArena harness, you must have the official WebArena repo and its Python dependencies available locally:

1) Clone the official repo and install deps (one-time):

```bash
cd /workspace/project
git clone https://github.com/web-arena-x/webarena
cd webarena && pip install -e .
```

2) Then run the evaluator:

```bash
poetry run python evaluation/benchmarks/webarena/eval_infer.py evaluation/evaluation_outputs/outputs/webarena/SOME_AGENT/EXP_NAME/output.jsonl
```

Notes:
- The evaluator expects WEBARENA_BASE_URL to be set and the WebArena services to be reachable.
- If you skip installing the official harness, you can still inspect output.jsonl manually or write your own scorer, but the script above will fail without the harness.

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).

## BrowsingAgent V1.0 result

Tested on BrowsingAgent V1.0

WebArena, 812 tasks (high cost, single run due to fixed task), max step 15

- GPT4o: 0.1478
- GPT3.5: 0.0517
