# SWE-bench-Live

<p align="center">
<a href="https://arxiv.org/abs/2505.23419">📃 Paper</a>
•
<a href="https://huggingface.co/SWE-bench-Live" >🤗 HuggingFace</a>
•
<a href="https://SWE-bench-Live.github.io" >📊 Leaderboard</a>
</p>

SWE-bench-Live is a live benchmark for issue resolving, providing a dataset that contains the latest issue tasks. This document explains how to run the evaluation of OpenHands on SWE-bench-Live.

Since SWE-bench-Live has an almost identical setting to SWE-bench, you only need to simply change the dataset name to `SWE-bench-Live/SWE-bench-Live`, the other parts are basically the same as running on SWE-bench.

## Setting Up

Set up the development environment and configure your LLM provider by following the [README](README.md).

## Running Inference

Use the same script, but change the dataset name to `SWE-bench-Live` and select the split (either `lite` or `full`). The lite split contains 300 instances from the past six months, while the full split includes 1,319 instances created after 2024.

```shell
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split]
```

In the original SWE-bench-Live paper, max_iterations is set to 100.

```shell
./evaluation/benchmarks/swe_bench/scripts/run_infer.sh llm.your_llm HEAD CodeActAgent 300 100 3 SWE-bench-Live/SWE-bench-Live lite
```

## Evaluating Results

After OpenHands generates patch results for each issue, we evaluate the results using the [SWE-bench-Live evaluation harness](https://github.com/microsoft/SWE-bench-Live).

Convert to the format of predictions for SWE benchmarks:

```shell
# You can find output.jsonl in evaluation/evaluation_outputs
python evaluation/benchmarks/swe_bench/scripts/live/convert.py --output_jsonl [path/to/evaluation/output.jsonl] > preds.jsonl
```

Please refer to the original [SWE-bench-Live repository](https://github.com/microsoft/SWE-bench-Live) to set up the evaluation harness and use the provided scripts to generate the evaluation report:

```shell
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench-Live/SWE-bench-Live \
    --split lite \
    --namespace starryzhang \
    --predictions_path preds.jsonl \
    --max_workers 10 \
    --run_id openhands
```

## Citation

```bibtex
@article{zhang2025swebenchgoeslive,
  title={SWE-bench Goes Live!},
  author={Linghao Zhang and Shilin He and Chaoyun Zhang and Yu Kang and Bowen Li and Chengxing Xie and Junhao Wang and Maoquan Wang and Yufan Huang and Shengyu Fu and Elsie Nallipogu and Qingwei Lin and Yingnong Dang and Saravan Rajmohan and Dongmei Zhang},
  journal={arXiv preprint arXiv:2505.23419},
  year={2025}
}
```
