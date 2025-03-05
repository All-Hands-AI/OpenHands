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
# use 2x resources for rollout since some codebases are pretty resource-intensive
export DEFAULT_RUNTIME_RESOURCE_FACTOR=2
echo "MODEL: $MODEL"
echo "EXP_NAME: $EXP_NAME"
DATASET="SWE-Gym/SWE-Gym"  # change this to the "/SWE-Gym-Lite" if you want to rollout the lite subset
SPLIT="train"

if [ -z "$ALLHANDS_API_KEY" ]; then
    echo "ALLHANDS_API_KEY is not set. Will rollout and evaluate locally using Docker. WARNING: A large value of N_WORKERS will result in a large number of Docker containers being spun up and may crash your machine."
    export RUNTIME=docker
else
    echo "ALLHANDS_API_KEY is set. Continuing rollout and evaluation with remote runtime..."
    export RUNTIME=remote
    export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev"
    export EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images"
fi

EVAL_LIMIT=3000
MAX_ITER=100


# ===== Run inference =====
source "evaluation/utils/version_control.sh"
get_openhands_version

echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "SPLIT: $SPLIT"

# Default to NOT use Hint
export USE_INSTANCE_IMAGE=true
export USE_HINT_TEXT=false
export RUN_WITH_BROWSING=false
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
EVAL_NOTE="$OPENHANDS_VERSION-no-hint-$EXP_NAME"

function run_eval() {
  local eval_note=$1
  COMMAND="poetry run python evaluation/benchmarks/swe_bench/run_infer.py \
    --agent-cls CodeActAgent \
    --llm-config $MODEL \
    --max-iterations $MAX_ITER \
    --eval-num-workers $N_WORKERS \
    --eval-note $eval_note \
    --dataset $DATASET \
    --split $SPLIT"

  if [ -n "$EVAL_LIMIT" ]; then
    echo "EVAL_LIMIT: $EVAL_LIMIT"
    COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
  fi

  # Run the command
  eval $COMMAND
}

for run_idx in $(seq 1 $N_RUNS); do

    while true; do
        echo "### Running inference... ###"
        unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push
        current_eval_note="$EVAL_NOTE-run_$run_idx"
        echo "EVAL_NOTE: $current_eval_note"
        INFER_OUTPUT=$(run_eval $current_eval_note)
        INFER_STATUS=$?  # Capture the exit status of run_infer.sh
        echo "INFER_STATUS: $INFER_STATUS"

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

        ./evaluation/utils/scripts/cleanup_remote_runtime.sh
    done

    # update the output with evaluation results
    echo "### Updating the output with evaluation results... ###"
    poetry run python evaluation/benchmarks/swe_bench/scripts/eval/update_output_with_eval.py $OUTPUT_FILE

    echo "### Combining the final completions... ###"
    poetry run python evaluation/benchmarks/swe_bench/scripts/eval/combine_final_completions.py $OUTPUT_FILE

    echo "### DONE for run $run_idx! ###"
    echo "You can find the final output at $(dirname $OUTPUT_FILE)/$FINAL_OUTPUT_FILE"
done
