#!/usr/bin/env bash

PROCESS_FILEPATH=$1
if [ -z "$PROCESS_FILEPATH" ]; then
    echo "Error: PROCESS_FILEPATH is empty. Usage: ./eval_infer.sh <output_file> [instance_id] [dataset_name] [split]"
    exit 1
fi

if [ ! -f $PROCESS_FILEPATH ]; then
    echo "Error: $PROCESS_FILEPATH is not a file"
    exit 1
fi

# If instance_id is empty, it means we want to eval on the whole $PROCESS_FILEPATH
# otherwise, we want to eval on the instance_id
INSTANCE_ID=$2
DATASET_NAME=${3:-"princeton-nlp/SWE-bench_Lite"}
SPLIT=${4:-"test"}
ENVIRONMENT=${5:-"local"}

echo "INSTANCE_ID: $INSTANCE_ID"
echo "DATASET_NAME: $DATASET_NAME"
echo "SPLIT: $SPLIT"

if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "modal" ]]; then
    echo "Error: ENVIRONMENT must be either 'local' or 'modal'"
    exit 1
fi

echo "ENVIRONMENT: $ENVIRONMENT"

PROCESS_FILEPATH=$(realpath $PROCESS_FILEPATH)
FILE_DIR=$(dirname $PROCESS_FILEPATH)
FILE_NAME=$(basename $PROCESS_FILEPATH)

echo "Evaluating $FILE_NAME @ $FILE_DIR"

# ================================================
# detect whether PROCESS_FILEPATH is in OH format or in SWE-bench format
echo "=============================================================="
echo "Detecting whether PROCESS_FILEPATH is in OH format or in SWE-bench format"
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

    # ==== Convert OH format to SWE-bench format ====
    echo "Merged output file with fine-grained report will be saved to $FILE_DIR"
    poetry run python3 evaluation/benchmarks/swe_bench/scripts/eval/convert_oh_output_to_swe_json.py $PROCESS_FILEPATH
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

RUN_ID=$(date +"%Y%m%d_%H%M%S")
N_PROCESS=4


MODAL_FLAG=""
if [[ "$ENVIRONMENT" == "modal" ]]; then
    MODAL_FLAG="--modal true"
fi

if [ -z "$INSTANCE_ID" ]; then
    echo "Running SWE-bench evaluation on the whole input file..."
    # Default to SWE-Bench-lite
    # change `--dataset_name` and `--split` to alter dataset

    poetry run python -m swebench.harness.run_evaluation \
        --dataset_name "$DATASET_NAME" \
        --split "$SPLIT" \
        --predictions_path $SWEBENCH_FORMAT_JSONL \
        --timeout 3600 \
        --cache_level instance \
        --max_workers $N_PROCESS \
        --run_id $RUN_ID \
        $MODAL_FLAG

    # get the "model_name_or_path" from the first line of the SWEBENCH_FORMAT_JSONL
    MODEL_NAME_OR_PATH=$(jq -r '.model_name_or_path' $SWEBENCH_FORMAT_JSONL | head -n 1)
    echo "MODEL_NAME_OR_PATH: $MODEL_NAME_OR_PATH"

    RESULT_OUTPUT_DIR=$(dirname $SWEBENCH_FORMAT_JSONL)
    echo "RESULT_OUTPUT_DIR: $RESULT_OUTPUT_DIR"

    # move the eval results to the target directory
    mkdir -p $RESULT_OUTPUT_DIR
    # rm eval_outputs directory if it exists
    if [ -d $RESULT_OUTPUT_DIR/eval_outputs ]; then
        rm -rf $RESULT_OUTPUT_DIR/eval_outputs
    fi

    mv logs/run_evaluation/$RUN_ID/$MODEL_NAME_OR_PATH $RESULT_OUTPUT_DIR
    mv $RESULT_OUTPUT_DIR/$MODEL_NAME_OR_PATH $RESULT_OUTPUT_DIR/eval_outputs
    echo "RUN_ID: $RUN_ID" > $RESULT_OUTPUT_DIR/run_id.txt

    # move report file
    REPORT_PATH=$MODEL_NAME_OR_PATH.$RUN_ID.json
    if [ -f $REPORT_PATH ]; then
        # check if $RESULT_OUTPUT_DIR/report.json exists
        if [ -f $RESULT_OUTPUT_DIR/report.json ]; then
            echo "Report file $RESULT_OUTPUT_DIR/report.json already exists. Overwriting..."
            if [ -f $RESULT_OUTPUT_DIR/report.json.bak ]; then
                rm $RESULT_OUTPUT_DIR/report.json.bak
            fi
            mv $RESULT_OUTPUT_DIR/report.json $RESULT_OUTPUT_DIR/report.json.bak
        fi

        mv $REPORT_PATH $RESULT_OUTPUT_DIR/report.json
    fi

    poetry run python evaluation/benchmarks/swe_bench/scripts/eval/update_output_with_eval.py $PROCESS_FILEPATH

else
    echo "Running SWE-bench evaluation on the instance_id: $INSTANCE_ID"
    poetry run python -m swebench.harness.run_evaluation \
        --dataset_name "$DATASET_NAME" \
        --split "$SPLIT" \
        --predictions_path $SWEBENCH_FORMAT_JSONL \
        --timeout 3600 \
        --instance_ids $INSTANCE_ID \
        --cache_level instance \
        --max_workers $N_PROCESS \
        --run_id $RUN_ID \
        $MODAL_FLAG
fi
