#!/bin/bash

# Function to run inference in parallel
run_parallel_inference() {
    local command=$1
    local mr_inputs_dir=$2
    local mr_outputs_dir=$3
    local eval_output_dir=$4
    local num_workers=$5

    echo "------ Checking number of input/output files ------"
    input_files=$(ls $mr_inputs_dir)
    output_files=$(ls $mr_outputs_dir)
    num_input_files=$(ls $mr_inputs_dir | wc -l)
    num_output_files=$(ls $mr_outputs_dir | wc -l)
    echo "# input files: $num_input_files"
    echo "# output files: $num_output_files"

    # Get the input files to run (input files - output files)
    input_files_to_run=$(comm -23 <(ls "$mr_inputs_dir" | sort) <(ls "$mr_outputs_dir" | sort))
    # return if empty
    if [ -z "$input_files_to_run" ]; then
        echo "No input files to run"
        return 1
    fi
    echo "# tasks remaining: $(echo "$input_files_to_run" | wc -l)"
    echo "------------------------------------------------"

    # Infer commands
    infer_cmd="$command --eval-map-reduce-read-input-file"
    # add mr_inputs_dir to each input file in input_files_to_run
    input_filepaths=$(
      echo "$input_files_to_run" | xargs -I {} echo "$mr_inputs_dir/{}"
    )

    echo "-------- Running inference in parallel --------"
    # Create an array of infer commands
    infer_cmds=()
    while IFS= read -r filepath; do
        infer_cmds+=(
          "echo 'Running $(basename $filepath)...'; $infer_cmd $filepath"
        )
    done <<< "$input_filepaths"

    echo "Number of infer commands to run: ${#infer_cmds[@]}"
    # Use GNU Parallel to run commands in parallel with progress bar
    printf '%s\n' "${infer_cmds[@]}" | \
    parallel --bar --ungroup --jobs $num_workers


    echo "-------- Inference completed, merging outputs to output.jsonl --------"
    poetry run python evaluation/utils/merge_folder_to_outputs.py $eval_output_dir
}
