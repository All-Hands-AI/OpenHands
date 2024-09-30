#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"
source "evaluation/utils/parallel_inference.sh"

# first check if parallel is installed
if ! command -v parallel &> /dev/null
then
    echo "GNU Parallel could not be found, please install it (e.g. sudo apt-get install parallel)"
    exit 1
fi

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
MAX_ITER=$5
NUM_WORKERS=$6
DATASET=$7
SPLIT=$8
N_RUNS=$9

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$MAX_ITER" ]; then
  echo "MAX_ITER not specified, use default 30"
  MAX_ITER=30
fi

if [ -z "$USE_INSTANCE_IMAGE" ]; then
  echo "USE_INSTANCE_IMAGE not specified, use default true"
  USE_INSTANCE_IMAGE=true
fi


if [ -z "$DATASET" ]; then
  echo "DATASET not specified, use default princeton-nlp/SWE-bench_Lite"
  DATASET="princeton-nlp/SWE-bench_Lite"
fi

if [ -z "$SPLIT" ]; then
  echo "SPLIT not specified, use default test"
  SPLIT="test"
fi

export USE_INSTANCE_IMAGE=$USE_INSTANCE_IMAGE
echo "USE_INSTANCE_IMAGE: $USE_INSTANCE_IMAGE"

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "SPLIT: $SPLIT"

# Default to NOT use Hint
if [ -z "$USE_HINT_TEXT" ]; then
  export USE_HINT_TEXT=false
fi
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
EVAL_NOTE="$AGENT_VERSION"
# if not using Hint, add -no-hint to the eval note
if [ "$USE_HINT_TEXT" = false ]; then
  EVAL_NOTE="$EVAL_NOTE-no-hint"
fi

if [ -n "$EXP_NAME" ]; then
  EVAL_NOTE="$EVAL_NOTE-$EXP_NAME"
fi
echo "EVAL_NOTE: $EVAL_NOTE"

unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push

run_inference() {
    local run_eval_note=$1
    echo "RUN_EVAL_NOTE: $run_eval_note"

    # Write inputs to mr_inputs
    local command="poetry run python evaluation/swe_bench/run_infer.py \
        --agent-cls $AGENT \
        --llm-config $MODEL_CONFIG \
        --max-iterations $MAX_ITER \
        --max-chars 10000000 \
        --eval-num-workers $NUM_WORKERS \
        --eval-note $run_eval_note \
        --dataset $DATASET \
        --split $SPLIT"
    if [ -n "$EVAL_LIMIT" ]; then
        echo "EVAL_LIMIT: $EVAL_LIMIT"
        command="$command --eval-n-limit $EVAL_LIMIT"
    fi

    # Run the command and get cmd outputs in a variable
    write_input_cmd="$command --eval-map-reduce-write-inputs"
    write_input_cmd_outputs=$(eval $write_input_cmd 2>&1)
    echo ""
    echo "------ Creating input files for map-reduce ------"
    echo "$write_input_cmd_outputs"
    echo "------------------------------------------------"
    eval_output_dir=$(echo "$write_input_cmd_outputs" | grep "Using evaluation output directory:" | awk '{print $NF}')
    mr_inputs_dir=$(realpath "$eval_output_dir/mr_inputs")
    mkdir -p $mr_inputs_dir
    mr_outputs_dir=$(realpath "$eval_output_dir/mr_outputs")
    mkdir -p $mr_outputs_dir
    echo "EVAL_OUTPUT_DIR: $eval_output_dir"
    echo "MR_INPUTS_DIR: $mr_inputs_dir"
    echo "MR_OUTPUTS_DIR: $mr_outputs_dir"
    echo ""

    # Call the parallel processing function from the library
    run_parallel_inference "$command" "$mr_inputs_dir" "$mr_outputs_dir" "$eval_output_dir" "$NUM_WORKERS"
}

if [ -n "$N_RUNS" ]; then
    echo "Running the same experiment $N_RUNS times and save results to different directories"
    for i in $(seq 1 $N_RUNS); do
        RUN_EVAL_NOTE="$EVAL_NOTE-run_$i"
        echo "Running iteration $i of $N_RUNS"
        run_inference "$RUN_EVAL_NOTE"
    done
else
    run_inference "$EVAL_NOTE"
fi

checkout_original_branch
