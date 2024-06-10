#!/bin/bash

echo "Cloning OpenDevin SWE-Bench Fork"
git clone https://github.com/OpenDevin/SWE-bench.git evaluation/swe_bench/eval_workspace/SWE-bench

echo "Pulling all evaluation dockers..."
evaluation/swe_bench/scripts/docker/pull_all_eval_docker.sh

echo "Downloading SWE-bench data..."
mkdir -p evaluation/swe_bench/eval_workspace/eval_data/instances
poetry run python3 evaluation/swe_bench/scripts/eval/download_swe_bench_data.py evaluation/swe_bench/eval_workspace/eval_data/instances
