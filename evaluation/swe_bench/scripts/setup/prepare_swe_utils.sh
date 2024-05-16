#!/bin/bash

set -e
EVAL_WORKSPACE="evaluation/swe_bench/eval_workspace"
mkdir -p $EVAL_WORKSPACE

# 1. Prepare REPO
echo "==== Prepare SWE-bench repo ===="
OD_SWE_BENCH_REPO_PATH="https://github.com/OpenDevin/OD-SWE-bench.git"
OD_SWE_BENCH_REPO_BRANCH="eval"
git clone -b $OD_SWE_BENCH_REPO_BRANCH $OD_SWE_BENCH_REPO_PATH $EVAL_WORKSPACE/OD-SWE-bench

# 2. Prepare DATA
echo "==== Prepare SWE-bench data ===="
EVAL_IMAGE=ghcr.io/opendevin/eval-swe-bench:builder_with_conda
EVAL_WORKSPACE=$(realpath $EVAL_WORKSPACE)
chmod +x $EVAL_WORKSPACE/OD-SWE-bench/swebench/harness/prepare_data.sh
if [ -d $EVAL_WORKSPACE/eval_data ]; then
    rm -r $EVAL_WORKSPACE/eval_data
fi
docker run \
    -v $EVAL_WORKSPACE:/workspace \
    -w /workspace \
    -u $(id -u):$(id -g) \
    -e HF_DATASETS_CACHE="/tmp" \
    --rm -it $EVAL_IMAGE \
    bash -c "cd OD-SWE-bench/swebench/harness && /swe_util/miniforge3/bin/conda run -n swe-bench-eval ./prepare_data.sh && mv eval_data /workspace/"
