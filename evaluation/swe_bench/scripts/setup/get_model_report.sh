#!/bin/bash

# Input arguments
output_file=""
model_name=""
dataset=""
num_processes=15
experiment_name=""

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --output-file) output_file="$2"; shift ;;
        --model-name) model_name="$2"; shift ;;
        --dataset) dataset="$2"; shift ;;
        --num-processes) num_processes="$2"; shift ;;
        --experiment-name) experiment_name="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if arguments are provided
if [[ -z "$output_file" || -z "$model_name" || -z "$dataset" ]]; then
    echo "output-file, model-name and dataset are required!"
    exit 1
fi
echo "output file: $output_file"
echo "model name: $model_name"
echo "dataset: $dataset"
echo "num processes: $num_processes"
if [ ! -z "$experiment_name" ]
then
    echo "use provided experiment name: $experiment_name"
else
    experiment_name=${model_name}__${dataset}
    echo "use generated experiment name: $experiment_name"
fi

# Run the evaluation script
mkdir -p $EVAL_DATA_DIR/eval_logs/$experiment_name
export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/harness/run_evaluation.py \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --temp_dir $EVAL_DATA_DIR/eval_temp \
    --testbed $EVAL_DATA_DIR/testbeds \
    --conda_path $MINICONDA3 \
    --predictions_path $output_file \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name \
    --num_processes $num_processes \
    --skip_existing \
    --timeout 1600 \
    --verbose

# Get the report
predictions_fname=$(basename $output_file)
cp $output_file $EVAL_DATA_DIR/eval_logs/$experiment_name
export PYTHONPATH=$OD_SWE_BENCH && cd $OD_SWE_BENCH && . $MINICONDA3/etc/profile.d/conda.sh && conda activate $MINICONDA3/envs/swe-bench-eval && python swebench/metrics/get_model_report.py \
	--model $model_name \
    --swe_bench_tasks $EVAL_DATA_DIR/instances/$dataset.json \
    --predictions_path $EVAL_DATA_DIR/eval_logs/$experiment_name/$predictions_fname \
    --log_dir $EVAL_DATA_DIR/eval_logs/$experiment_name/$model_name
