#!/bin/bash

echo "Pulling all evaluation docker..."
evaluation/swe_bench/scripts/docker/pull_all_eval_docker.sh

echo "Downloading SWE-bench data..."
mkdir -p evaluation/swe_bench/eval_workspace/eval_data/instances
python3 evaluation/swe_bench/scripts/eval/download_swe_bench_data.py evaluation/swe_bench/eval_workspace/eval_data/instances
