# Evaluate OpenHands on NoCode-bench

## LLM Setup

Please follow [here](../../README.md#setup).


## Docker image download

Evaluating OpenHands on NoCode-bench need instance-level docker image.
Please follow the instructions of NoCode-bench image setup to build or download all instance-level dokcer [here](https://github.com/NoCode-bench/NoCode-bench).

## Generate patch

Please follow the instructions [here](../swe_bench/README.md#running-locally-with-docker)
For example,
```bash
bash ./evaluation/benchmarks/nocode_bench/scripts/run_infer_nc.sh llm.claude HEAD CodeActAgent 114 100 10 NoCode-bench/NoCode-bench_Verified test
```
The results will be generated in evaluation/evaluation_outputs/outputs/XXX/CodeActAgent/YYY/output.jsonl.

## Runing evaluation

First, install [NoCode-bench](https://github.com/NoCode-bench/NoCode-bench).

Second, convert the output.jsonl to patch.jsonl with [script](scripts/eval/convert.py).

```bash
python evaluation/benchmarks/multi_swe_bench/scripts/eval/convert.py
```

Finally, evaluate with NoCode-bench.

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python ./evaluation/eval.py \
    --predictions_path ./all_preds.jsonl \  # <path_to_your_predictions>
    --log_dir ./evaluation/logs \ # <path_to_your_log_dir>
    --bench_tasks NoCode-bench/NoCode-bench_Verified \ # <dataset_name>
    --max_workers 110 \ # <number_of_workers>
    --output_file eval_result.txt \ # <path_to_your_output_file>
    --image_level repo \ # <cache_image_level>
    --timeout 600 \ # <timeout_in_seconds>
    --proxy None # <proxy_if_needed>
```
