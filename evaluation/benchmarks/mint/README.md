# MINT Benchmark

This folder contains the evaluation harness for the [MINT benchmark](https://arxiv.org/abs/2309.10691) on LLMs' ability to solve tasks with multi-turn interactions.

We support evaluation of the [Eurus subset focus on math and code reasoning](https://arxiv.org/abs/2404.02078), including MATH, MMLU, TheoremQA, HumanEval, MBPP.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Start the evaluation

We are using the MINT dataset hosted on [Hugging Face](https://huggingface.co/datasets/ryanhoangt/xingyaoww-mint-bench).

Following is the basic command to start the evaluation. Currently, the only agent supported with MINT is `CodeActAgent`.

```bash
./evaluation/benchmarks/mint/scripts/run_infer.sh [model_config] [git-version] [subset] [eval_limit]
```

where `model_config` is mandatory, while others are optional.

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your LLM settings, as defined in your `config.toml`.

- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

- `subset`, e.g. `math`, is the subset of the MINT benchmark to evaluate on, defaulting to `math`. It can be either: `math`, `gsm8k`, `mmlu`, `theoremqa`, `mbpp`,`humaneval`.

- `eval_limit`, e.g. `2`, limits the evaluation to the first `eval_limit` instances, defaulting to all instances.

Note: in order to use `eval_limit`, you must also set `subset`.

For example,

```bash
./evaluation/benchmarks/mint/scripts/run_infer.sh eval_gpt4_1106_preview 0.6.2 gsm8k 3
```

## Reference

```
@misc{wang2024mint,
    title={MINT: Evaluating LLMs in Multi-turn Interaction with Tools and Language Feedback},
    author={Xingyao Wang and Zihan Wang and Jiateng Liu and Yangyi Chen and Lifan Yuan and Hao Peng and Heng Ji},
    year={2024},
    eprint={2309.10691},
    archivePrefix={arXiv},
    primaryClass={cs.CL}
}
```
