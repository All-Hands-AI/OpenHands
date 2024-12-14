# Evaluating GPQA (A Graduate-Level Google-Proof Q&A Benchmark) with OpenHands

Implements the evaluation of agents on the GPQA benchmark introduced in [GPQA: A Graduate-Level Google-Proof Q&A Benchmark](https://arxiv.org/abs/2308.07124).

This code implements the evaluation of agents on the GPQA Benchmark with Open Book setting.

- The benchmark consists of 448 high-quality and extremely difficult multiple-choice questions in the domains of biology, physics, and chemistry. The questions are intentionally designed to be "Google-proof," meaning that even highly skilled non-expert validators achieve only 34% accuracy despite unrestricted access to the web.
- Even experts in the corresponding domains achieve only 65% accuracy.
- State-of-the-art AI systems achieve only 39% accuracy on this challenging dataset.

**Note**
Accurate solving of above graduate level questions would require both tool use (e.g., python for calculations) and web-search for finding related facts as information required for the questions might not be part of the LLM knowledge / training data.

Further references:

- <https://arxiv.org/pdf/2311.12022>
- <https://paperswithcode.com/dataset/gpqa>
- <https://github.com/idavidrein/gpqa>

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on GPQA Benchmark

'gpqa_main', 'gqpa_diamond', 'gpqa_experts', 'gpqa_extended' -- data split options
From the root of the OpenHands repo, run the following command:

```bash
./evaluation/benchmarks/gpqa/scripts/run_infer.sh [model_config_name] [git-version] [num_samples_eval] [data_split] [AgentClass]
```

You can replace `model_config_name` with any model you set up in `config.toml`.

- `model_config_name`: The model configuration name from `config.toml` that you want to evaluate.
- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.
- `num_samples_eval`: Number of samples to evaluate (useful for testing and debugging).
- `data_split`: The data split to evaluate on. Must be one of `gpqa_main`, `gqpa_diamond`, `gpqa_experts`, `gpqa_extended`. Defaults to `gpqa_diamond` as done in the paper.
- `AgentClass`: The agent class to use for evaluation. Currently only supports `CodeActAgent` for CodeActAgent.
