#!/bin/bash

# Initialize variables
output_file=""
model_name=""
dataset=""

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --output-file) output_file="$2"; shift ;;
        --model-name) model_name="$2"; shift ;;
        --dataset) dataset="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if parameters are provided
if [[ -z "$output_file" || -z "$model_name" || -z "$dataset" ]]; then
    echo "output-file, model-name and dataset are required."
    exit 1
fi

echo "output file: $output_file"
echo "model name: $model_name"
echo "dataset: $dataset"

# 1. Run the evaluation script

if [ -z "$EVAL_DATA_DIR" ]; then
    echo "EVAL_DATA_DIR is not set."
    exit 1
fi

export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/harness/run_evaluation.py \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --temp_dir $EVAL_DATA_DIR/eval_temp \
    --testbed $EVAL_DATA_DIR/testbeds \
    --conda_path $MINICONDA3 \
    --predictions_path $output_file \
    --log_dir $EVAL_DATA_DIR/eval_logs \
    --num_processes 15 \
    --skip_existing \
    --timeout 900 \
    --verbose

# 2. Get the report
predictions_fname=$(basename $output_file)
cp $output_file $EVAL_DATA_DIR/eval_logs
export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/metrics/get_model_report.py \
	--model $model_name \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --predictions_path $EVAL_DATA_DIR/eval_logs/$predictions_fname \
    --log_dir $EVAL_DATA_DIR/eval_logs




