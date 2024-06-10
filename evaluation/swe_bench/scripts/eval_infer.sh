#!/bin/bash

PROCESS_FILEPATH=$1
if [ -z "$PROCESS_FILEPATH" ]; then
    echo "Error: PROCESS_FILEPATH is empty. Usage: ./eval_infer.sh <output_file>"
    exit 1
fi

if [ ! -f $PROCESS_FILEPATH ]; then
    echo "Error: $PROCESS_FILEPATH is not a file"
    exit 1
fi

# If instance_id is empty, it means we want to eval on the whole $PROCESS_FILEPATH
# otherwise, we want to eval on the instance_id
INSTANCE_ID=$2
echo "INSTANCE_ID: $INSTANCE_ID"

PROCESS_FILEPATH=$(realpath $PROCESS_FILEPATH)
FILE_DIR=$(dirname $PROCESS_FILEPATH)
FILE_NAME=$(basename $PROCESS_FILEPATH)
mkdir -p $FILE_DIR/logs
mkdir -p $FILE_DIR/swe_bench_format

echo "Evaluating $FILE_NAME @ $FILE_DIR"
DOCKERHUB_NAMESPACE="xingyaoww"
SWEBENCH_TASKS=$(realpath evaluation/swe_bench/eval_workspace/eval_data/instances/swe-bench-lite-all.json)
export SWEBENCH_DOCKER_FORK_DIR=$(realpath evaluation/swe_bench/eval_workspace/SWE-bench-docker)

# ================================================
# detect whether PROCESS_FILEPATH is in OD format or in SWE-bench format
echo "=============================================================="
echo "Detecting whether PROCESS_FILEPATH is in OD format or in SWE-bench format"
echo "=============================================================="
# SWE-bench format is a JSONL where every line has three fields: model_name_or_path, instance_id, and model_patch
function is_swebench_format() {
    # Read the first line of the file
    read -r first_line < "$PROCESS_FILEPATH"

    # Use jq to check if the first line has the required fields
    echo "$first_line" | jq -e '. | has("model_name_or_path") and has("instance_id") and has("model_patch")' > /dev/null

    if [ $? -ne 0 ]; then
        return 1 # Return 1 if the first line does not have the required fields
    fi

    return 0 # Return 0 if the first line has the required fields
}
# Call the function with the file path
is_swebench_format "$PROCESS_FILEPATH"
IS_SWEBENCH_FORMAT=$?
# Use the result in an if-else statement
if [ $IS_SWEBENCH_FORMAT -eq 0 ]; then
    echo "The file IS in SWE-bench format."
    SWEBENCH_FORMAT_JSONL=$PROCESS_FILEPATH
else
    echo "The file IS NOT in SWE-bench format."

    # ==== Convert OD format to SWE-bench format ====
    echo "Merged output file with fine-grained report will be saved to $FILE_DIR"
    poetry run python3 evaluation/swe_bench/scripts/eval/convert_od_output_to_swe_json.py $PROCESS_FILEPATH
    # replace .jsonl with .swebench.jsonl in filename
    SWEBENCH_FORMAT_JSONL=${PROCESS_FILEPATH/.jsonl/.swebench.jsonl}
    echo "SWEBENCH_FORMAT_JSONL: $SWEBENCH_FORMAT_JSONL"
    # assert that the file exists
    if [ ! -f $SWEBENCH_FORMAT_JSONL ]; then
        echo "Error: $SWEBENCH_FORMAT_JSONL does not exist. There is probably an error in the conversion process."
        exit 1
    fi
    SWEBENCH_FORMAT_JSONL=$(realpath $SWEBENCH_FORMAT_JSONL)
fi
# ================================================

echo "=============================================================="
echo "Running SWE-bench evaluation"
echo "=============================================================="

if [ -z "$INSTANCE_ID" ]; then
    echo "Running SWE-bench evaluation on the whole input file..."

    poetry run python $SWEBENCH_DOCKER_FORK_DIR/run_evaluation.py \
        --predictions_path $SWEBENCH_FORMAT_JSONL \
        --log_dir $FILE_DIR/logs \
        --swe_bench_tasks $SWEBENCH_TASKS \
        --namespace $DOCKERHUB_NAMESPACE \
        --timeout 1800

else
    echo "Running SWE-bench evaluation on the instance_id: $INSTANCE_ID"
    poetry run python $SWEBENCH_DOCKER_FORK_DIR/run_single_instance.py \
        --predictions_path $SWEBENCH_FORMAT_JSONL \
        --swe_bench_tasks $SWEBENCH_TASKS \
        --namespace $DOCKERHUB_NAMESPACE \
        --instance_id $INSTANCE_ID
fi

poetry run python $SWEBENCH_DOCKER_FORK_DIR/generate_report.py \
    --predictions_path $SWEBENCH_FORMAT_JSONL \
    --log_dir $FILE_DIR/logs \
    --output_dir $FILE_DIR \
    --swe_bench_tasks $SWEBENCH_TASKS
