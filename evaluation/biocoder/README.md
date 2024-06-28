# BioCoder Evaluation with Opendevin

Implements evaluation of agents on BioCoder from the BioCoder benchmark introduced in [BioCoder: A Benchmark for Bioinformatics Code Generation with Large Language Models](https://arxiv.org/abs/2308.16458). Please see [here](https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack.py) for the reference implementation used in the paper.

## Setup Environment

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.


## Configure OpenDevin and your LLM
Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md) for how to set this up.

## BioCoder Docker Image
In the opendevin branch of the Biocoder repository, we have slightly modified our original Docker image to work with the OpenDevin environment. In the Docker image are testing scripts (`/testing/start_test_opendevin.py` and aux files in `/testing_files/`) to assist with evaluation. Additionally, we have installed all dependencies, including OpenJDK, mamba (with Python 3.6), and many system libraries. Notably, we have **not** packaged all repositories into the image, so they are downloaded at runtime.

**Before first execution, pull our Docker image with the following command**
```bash
docker pull public.ecr.aws/i5g0m1f6/eval_biocoder:v1.0
```

To reproduce this image, please see the Dockerfile_Opendevin in the `biocoder` repository.

## Start the evaluation


```bash
./evaluation/biocoder/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
```

where `model_config` is mandatory, while `git-version`, `agent`, `dataset` and `eval_limit` are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenDevin version you would
like to evaluate. It could also be a release tag like `0.6.2`.

- `agent`, e.g. `CodeActAgent`, is the name of the agent for benchmarks, defaulting
to `CodeActAgent`.

- `eval_limit`, e.g. `10`, limits the evaluation to the first `eval_limit` instances. By default it infers all instances.

Let's say you'd like to run 1 instance using `eval_gpt4_1106_eval_gpt4o_2024_05_13preview` and CodeActAgent
with OpenDevin version 0.6.2, then your command would be:

## Examples

```bash
./evaluation/biocoder/scripts/run_infer.sh eval_gpt4o_2024_05_13 0.6.2 CodeActAgent 1
```

## Reference
```
@misc{tang2024biocoder,
      title={BioCoder: A Benchmark for Bioinformatics Code Generation with Large Language Models},
      author={Xiangru Tang and Bill Qian and Rick Gao and Jiakang Chen and Xinyun Chen and Mark Gerstein},
      year={2024},
      eprint={2308.16458},
      archivePrefix={arXiv},
      primaryClass={cs.LG}
}
```
