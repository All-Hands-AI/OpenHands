#!/bin/bash

FOLDER_PATH=$1
NEW_FOLDER_PATH=${FOLDER_PATH}.swebench_submission
mkdir -p $NEW_FOLDER_PATH

# Build all_preds.jsonl
poetry run python evaluation/benchmarks/swe_bench/scripts/eval/convert_oh_output_to_swe_json.py $FOLDER_PATH/output.jsonl
mv $FOLDER_PATH/output.swebench.jsonl $NEW_FOLDER_PATH/all_preds.jsonl

# Build trajs/
mkdir -p $NEW_FOLDER_PATH/trajs
for instance_dir in $FOLDER_PATH/llm_completions/*/; do
    instance_id=$(basename "$instance_dir")
    latest_json=$(ls -t "$instance_dir"/*.json | head -n1)
    if [ -n "$latest_json" ]; then
        cat "$latest_json" | jq -r '.messages' > "$NEW_FOLDER_PATH/trajs/$instance_id.json"
    fi
done

# Build logs/
# check if $FOLDER_PATH/eval_outputs exists, if so copy over - else raise error
if [ -d "$FOLDER_PATH/eval_outputs" ]; then
    cp -r $FOLDER_PATH/eval_outputs $NEW_FOLDER_PATH/logs
else
    echo "Error: $FOLDER_PATH/eval_outputs does not exist. You should run the local docker eval_infer.sh first."
    exit 1
fi
