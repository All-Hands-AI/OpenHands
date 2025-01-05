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

while true; do
    echo "### Running inference... ###"
    # Capture the output in a variable while also printing to stdout
    INFER_OUTPUT=$(./evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
        $MODEL HEAD CodeActAgent \
        $EVAL_LIMIT $MAX_ITER $N_WORKERS \
        $DATASET $SPLIT $N_RUNS | tee >(cat 1>&2))

    INFER_STATUS=$?  # Capture the exit status of run_infer.sh

    echo "### Cleaning up remote runtime... ###"
    ./evaluation/utils/scripts/cleanup_remote_runtime.sh

    if [ $INFER_STATUS -eq 0 ]; then
        echo "### Inference completed successfully. ###"
        break
    else
        echo "### Inference failed with exit code $INFER_STATUS. Retrying... ###"
    fi
done

# Extract the output directory using the special delimiters
OUTPUT_FILE=$(echo "$INFER_OUTPUT" | grep -o '### OUTPUT FILE:.* ###' | sed 's/### OUTPUT FILE: \(.*\) ###/\1/')
echo "Got OUTPUT_FILE: $OUTPUT_FILE"

while true; do
    echo "### Evaluating on $OUTPUT_FILE ... ###"
    COMMAND="poetry run python evaluation/benchmarks/swe_bench/eval_infer.py \
    --eval-num-workers $((N_WORKERS * 2)) \
    --input-file $OUTPUT_FILE \
    --dataset $DATASET \
    --split $SPLIT"

    if [ -n "$EVAL_LIMIT" ]; then
    echo "EVAL_LIMIT: $EVAL_LIMIT"
    COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
    fi
    echo "Running command: $COMMAND"
    # Run the command
    eval $COMMAND
    EVAL_STATUS=$?
    if [ $EVAL_STATUS -eq 0 ]; then
        echo "### Evaluation completed successfully. ###"
        break
    else
        echo "### Evaluation failed with exit code $EVAL_STATUS. Retrying... ###"
    fi
done

# update the output with evaluation results
echo "### Updating the output with evaluation results... ###"
poetry run python evaluation/benchmarks/swe_bench/scripts/eval/update_output_with_eval.py $OUTPUT_FILE

echo "### Combining the final completions... ###"
poetry run python evaluation/benchmarks/swe_bench/scripts/eval/combine_final_completions.py $OUTPUT_FILE

echo "### DONE! ###"
echo "You can find the final output at $(dirname $OUTPUT_FILE)/$FINAL_OUTPUT_FILE"
