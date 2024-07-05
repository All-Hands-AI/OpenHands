# WebArena Evaluation with OpenDevin Browsing Agents

This folder contains evaluation for [MiniWoB++](https://miniwob.farama.org/) benchmark, powered by [BrowserGym](https://github.com/ServiceNow/BrowserGym) for easy evaluation of how well an agent capable of browsing can perform on synthetic web browsing tasks.

## Setup OpenDevin Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
ssh_hostname = "localhost"

[sandbox]
box_type = "ssh"
timeout = 120

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

## Setup MiniWoB++ Environment and Environment Variables of MiniWoB++
MiniWoB++ requires you to set up websites containing a static website that is accessible via URL to the machine running the OpenDevin agents.

- Clone miniwob (use a specific frozen commit for reproducibility)
```sh
git clone git@github.com:Farama-Foundation/miniwob-plusplus.git
git -C "./miniwob-plusplus" reset --hard 7fd85d71a4b60325c6585396ec4f48377d049838
```

- Setup Miniwob URL (change `PATH_TO_MINIWOB_CLONED_REPO` here to the absolute path to your `miniwob-plusplus` folder) in `evaluation/miniwob/scripts/run_infer.sh`
```sh
export MINIWOB_URL="file://<PATH_TO_MINIWOB_CLONED_REPO>/miniwob/html/miniwob/"
```

## Test if your environment works

Access with browser the above MiniWoB URLs and see if they load correctly.

## Run Evaluation

```sh
bash evaluation/miniwob/scripts/run_infer.sh
```

Results will be in `evaluation/evaluation_outputs/outputs/miniwob/`

To calculate the average reward, run:

```sh
poetry run python evaluation/miniwob/get_success_rate.py evaluation/evaluation_outputs/outputs/miniwob/SOME_AGENT/EXP_NAME/output.jsonl
```

## Submit your evaluation results

You can start your own fork of [our huggingface evaluation outputs](https://huggingface.co/spaces/OpenDevin/evaluation) and submit a PR of your evaluation results following the guide [here](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions#pull-requests-and-discussions).


## BrowsingAgent V1.0 result

Tested on BrowsingAgent V1.0

MiniWoB++, 125 tasks (3 runs due to random init task), max step 10

- GPT4o: 0.384, 0.416, 0.424, avg: 0.408
- GPT3.5: 0.288, 0.256, 0.272, avg: 0.272
