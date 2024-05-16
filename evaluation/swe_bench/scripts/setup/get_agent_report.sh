#!/bin/bash

# Initialize variables
output_file=""
agent_name=""
dataset=""
num_processes=15
experiment_name=""
merge_report=false

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --output-file) output_file="$2"; shift ;;
        --agent-name) agent_name="$2"; shift ;;
        --dataset) dataset="$2"; shift ;;
        --num-processes) num_processes="$2"; shift ;;
        --experiment-name) experiment_name="$2"; shift ;;
        --merge-report) merge_report=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if arguments are provided
if [[ -z "$output_file" || -z "$agent_name" || -z "$dataset" ]]; then
    echo "output-file, agent-name and dataset are required!"
    exit 1
fi
echo "output file: $output_file"
echo "agent name: $agent_name"
echo "dataset: $dataset"
echo "num processes: $num_processes"
if [ ! -z "$experiment_name" ]
then
    echo "use provided experiment name: $experiment_name"
else
    current_folder=$(basename $(dirname $output_file))
    parent_foler=$(basename $(dirname $(dirname $output_file)))
    experiment_name="${parent_foler}_${current_folder}"
    echo "use generated experiment name: $experiment_name"
fi

# Convert the agent output to the SWE-Bench format
if [ -z "$EVAL_DATA_DIR" ]; then
    echo "EVAL_DATA_DIR is not set."
    exit 1
fi
target_file="${EVAL_DATA_DIR}/outputs/${experiment_name}_${dataset}.json"
python process_output_json_file.py $output_file $agent_name $target_file

# Run the evaluation script
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
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --temp_dir $EVAL_DATA_DIR/eval_temp \
    --testbed $EVAL_DATA_DIR/testbeds \
    --conda_path $MINICONDA3 \
    --predictions_path $target_file \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name \
    --num_processes 15 \
    --skip_existing \
    --timeout 1600 \
    --verbose

# Get the report
cp $target_file $EVAL_DATA_DIR/eval_logs/$experiment_name
export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/metrics/get_model_report.py \
	--model $agent_name \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --predictions_path $EVAL_DATA_DIR/eval_logs/$experiment_name/${experiment_name}_${dataset}.json \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name/$agent_name

# Merge report to the agent output
if [ "$merge_report" = true ]; then
    cd /swe_util && python merge_fine_grained_report.py --od_output_file $output_file \
    --fine_grained_report_file $EVAL_DATA_DIR/eval_logs/$experiment_name/${experiment_name}_${dataset}.report.json
fi
