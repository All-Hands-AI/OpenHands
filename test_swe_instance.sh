#!/bin/bash

# Simple script to test a single SWE instance
# Usage: ./test_swe_instance.sh <dataset_file> <instance_id> <output_file>

set -e

if [ $# -ne 3 ]; then
    echo "Usage: $0 <dataset_file> <instance_id> <output_file>"
    echo "Example: $0 ./datasets/jackson_3600_3630_b.jsonl fasterxml__jackson-databind-3608 ./datasets/jackson_3600_3630_b_output1.jsonl"
    exit 1
fi

DATASET_FILE=$1
INSTANCE_ID=$2
OUTPUT_FILE=$3

# Check if dataset file exists
if [ ! -f "$DATASET_FILE" ]; then
    echo "Error: Dataset file '$DATASET_FILE' not found!"
    echo "Please make sure the dataset file exists."
    exit 1
fi

# Convert dataset if needed
CONVERTED_FILE="${DATASET_FILE%.*}_converted.jsonl"
if [ ! -f "$CONVERTED_FILE" ]; then
    echo "Converting dataset to SWE-bench format..."
    python convert_dataset.py "$DATASET_FILE" "$CONVERTED_FILE"
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

echo "Running SWE instance test..."
echo "Dataset: $CONVERTED_FILE"
echo "Instance ID: $INSTANCE_ID"
echo "Output: $OUTPUT_FILE"

# Default configuration
AGENT_CLS="CodeActAgent"
MAX_ITERATIONS=100
LLM_CONFIG="claude20241022"
EVAL_NOTE="single-instance-test"

# Run the evaluation using the multi_swe_bench runner
python evaluation/benchmarks/multi_swe_bench/run_infer.py \
    --agent-cls "$AGENT_CLS" \
    --llm-config "$LLM_CONFIG" \
    --max-iterations "$MAX_ITERATIONS" \
    --eval-num-workers 1 \
    --eval-note "$EVAL_NOTE" \
    --eval-ids "$INSTANCE_ID" \
    --dataset "$CONVERTED_FILE" \
    --split train

echo "Test completed. Check the evaluation output directory for results."
echo "Results should be in: evaluation/evaluation_outputs/outputs/"

# Find and copy the output file to the desired location
OUTPUT_DIR_PATTERN="evaluation/evaluation_outputs/outputs/.*${EVAL_NOTE}/output.jsonl"
ACTUAL_OUTPUT=$(find evaluation/evaluation_outputs -name "output.jsonl" -path "*${EVAL_NOTE}*" | head -1)

if [ -n "$ACTUAL_OUTPUT" ] && [ -f "$ACTUAL_OUTPUT" ]; then
    echo "Copying results from $ACTUAL_OUTPUT to $OUTPUT_FILE"
    cp "$ACTUAL_OUTPUT" "$OUTPUT_FILE"
    echo "Results copied to: $OUTPUT_FILE"
else
    echo "Output file not found. Check the evaluation directory:"
    find evaluation/evaluation_outputs -name "output.jsonl" -path "*${EVAL_NOTE}*" | head -3
fi