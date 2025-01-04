#!/bin/bash

# NOTE: this script is for rolling out the SWE-Gym dataset for **TRAINING**
# For more information, please refer to
# 1. the Github Repo: https://github.com/SWE-Gym/SWE-Gym
# 2. the paper: https://arxiv.org/abs/2412.21139

MODEL=$1  # eg your llm config name in config.toml (eg: "llm.claude-3-5-sonnet-20241022-t05")
EXP_NAME=$2 # "train-t05"
N_WORKERS=${3:-64}
N_RUNS=${4:-1}

export EXP_NAME=$EXP_NAME
export DEFAULT_RUNTIME_RESOURCE_FACTOR=2  # use 2x resources for rollout since some codebase are pretty resource-intensive
echo "MODEL: $MODEL"
echo "EXP_NAME: $EXP_NAME"
DATASET="SWE-Gym/SWE-Gym"  # change this to the "/SWE-Gym-Lite" if you want to rollout the lite subset
SPLIT="train"

if [ -z "$ALLHANDS_API_KEY" ]; then
    echo "ALLHANDS_API_KEY is not set. Please set it and run the script again."
    exit 1
fi

export RUNTIME=remote
export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev"
export EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images"

EVAL_LIMIT=500
MAX_ITER=100

./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
    $MODEL HEAD CodeActAgent \
    $EVAL_LIMIT $MAX_ITER $N_WORKERS \
    $DATASET $SPLIT $N_RUNS
