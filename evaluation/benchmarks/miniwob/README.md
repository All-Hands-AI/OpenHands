# Mini-World of Bits Evaluation with OpenHands Browsing Agents

This folder contains evaluation for [MiniWoB++](https://miniwob.farama.org/) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on synthetic web browsing tasks.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Test if your environment works

Access with browser the above MiniWoB URLs and see if they load correctly.

## Run Evaluation

```sh
./evaluation/benchmarks/miniwob/scripts/run_infer.sh llm.claude-35-sonnet-eval
```

### Run Inference on `RemoteRuntime` (experimental)

This is in limited beta. Contact Xingyao over slack if you want to try this out!

```bash
./evaluation/benchmarks/miniwob/scripts/run_infer.sh [model_config] [git-version] [agent] [note] [eval_limit] [num_workers]

# Example - This runs evaluation on BrowsingAgent for 125 instances on miniwob, with 2 workers running in parallel
export ALLHANDS_API_KEY="YOUR-API-KEY"
export RUNTIME=remote
export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev"
./evaluation/benchmarks/miniwob/scripts/run_infer.sh llm.eval HEAD BrowsingAgent "" 125 2
```

Results will be in `evaluation/evaluation_outputs/outputs/miniwob/`

To calculate the average reward, run:

```sh
poetry run python evaluation/benchmarks/miniwob/get_success_rate.py evaluation/evaluation_outputs/outputs/miniwob/SOME_AGENT/EXP_NAME/output.jsonl
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenHands/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).

## BrowsingAgent V1.0 result

Tested on BrowsingAgent V1.0

MiniWoB++, 125 tasks (3 runs due to random init task), max step 10

- GPT4o: 0.384, 0.416, 0.424, avg: 0.408
- GPT3.5: 0.288, 0.256, 0.272, avg: 0.272
