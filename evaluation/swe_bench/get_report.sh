#!/bin/bash

# Initialize variables
output_file=""
model_or_agent_name=""
dataset=""

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --output-file) output_file="$2"; shift ;;
        --model-or-agent-name) model_or_agent_name="$2"; shift ;;
        --dataset) dataset="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if parameters are provided
if [[ -z "$output_file" || -z "$model_or_agent_name" || -z "$dataset" ]]; then
    echo "output-file, model-or-agent-name and dataset are required."
    exit 1
fi

echo "output file: $output_file"
echo "model or agent name: $model_or_agent_name"
echo "dataset: $dataset"


# 1. Convert the output file
# Extract experiment name from the path
if [ ! -f $output_file ]; then
    echo "Output file does not exist."
    exit 1
fi
experiment_name=$(basename $(dirname $output_file))
echo "experiment name: $experiment_name"

# Path to store the final output
if [ -z "$EVAL_DATA_DIR" ]; then
    echo "EVAL_DATA_DIR is not set."
    exit 1
fi
target_file="${EVAL_DATA_DIR}/outputs/${experiment_name}_${dataset}.json"

# Process the JSONL file

python process_output_json_file.py $output_file $model_or_agent_name $target_file

# 2. Run the evaluation script
if [ -z "$OD_SWE_BENCH" ]; then
    echo "OD_SWE_BENCH is not set."
    exit 1
fi
if [ -z "$MINICONDA3" ]; then
    echo "MINICONDA3 is not set."
    exit 1
fi

mkdir -p $EVAL_DATA_DIR/eval_logs/$experiment_name
export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/harness/run_evaluation.py \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/swe-bench-test.json \
    --temp_dir $EVAL_DATA_DIR/eval_temp \
    --testbed $EVAL_DATA_DIR/testbeds \
    --conda_path $MINICONDA3 \
    --predictions_path $target_file \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name \
    --num_processes 15 \
    --skip_existing \
    --timeout 900 \
    --verbose

# 3. Get the report
cp $target_file $EVAL_DATA_DIR/eval_logs
SWE_BENCH_PATH=/shared/bowen/codellm/swe/OD-SWE-bench
TEMP=/shared/bowen/codellm/swe/temp
export PYTHONPATH=$SWE_BENCH_PATH && cd $SWE_BENCH_PATH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/metrics/get_model_report.py \
	--model $model_or_agent_name \
    --swe_bench_tasks $TEMP/harness_materials/processed/swe-bench-lite-test.json \
    --predictions_path $EVAL_DATA_DIR/eval_logs/${experiment_name}_${dataset}.json \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name/$model_or_agent_name




