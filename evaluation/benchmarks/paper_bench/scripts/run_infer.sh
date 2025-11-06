#!/usr/bin/env bash


# Exit on any error would be useful for debugging
if [ -n "$DEBUG" ]; then
    set -e
fi

# AGENT_LLM_CONFIG is the config name for the agent LLM
# In config.toml, you should have a section with the name
# [llm.<AGENT_LLM_CONFIG>], e.g. [llm.agent]
AGENT_LLM_CONFIG="agent"

# OUTPUTS_PATH is the path to save trajectories and evaluation results
OUTPUTS_PATH="outputs"


# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent-llm-config)
            AGENT_LLM_CONFIG="$2"
            shift 2
            ;;
        --agent-config)
            AGENT_CONFIG="$2"
            shift 2
            ;;
        --outputs-path)
            OUTPUTS_PATH="$2"
            shift 2
            ;;
        --start-percentile)
            START_PERCENTILE="$2"
            shift 2
            ;;
        --end-percentile)
            END_PERCENTILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Convert outputs_path to absolute path
if [[ ! "$OUTPUTS_PATH" = /* ]]; then
    # If path is not already absolute (doesn't start with /), make it absolute
    OUTPUTS_PATH="$(cd "$(dirname "$OUTPUTS_PATH")" 2>/dev/null && pwd)/$(basename "$OUTPUTS_PATH")"
fi

: "${START_PERCENTILE:=0}"  # Default to 0 percentile (first line)
: "${END_PERCENTILE:=100}"  # Default to 100 percentile (last line)

# Validate percentile ranges if provided
if ! [[ "$START_PERCENTILE" =~ ^[0-9]+$ ]] || ! [[ "$END_PERCENTILE" =~ ^[0-9]+$ ]]; then
    echo "Error: Percentiles must be integers"
    exit 1
fi

if [ "$START_PERCENTILE" -ge "$END_PERCENTILE" ]; then
    echo "Error: Start percentile must be less than end percentile"
    exit 1
fi

if [ "$START_PERCENTILE" -lt 0 ] || [ "$END_PERCENTILE" -gt 100 ]; then
    echo "Error: Percentiles must be between 0 and 100"
    exit 1
fi

echo "Using agent LLM config: $AGENT_LLM_CONFIG"
echo "Outputs path: $OUTPUTS_PATH"
echo "Start Percentile: $START_PERCENTILE"
echo "End Percentile: $END_PERCENTILE"

total_lines=$(cat tasks.md | wc -l)

# Calculate line numbers based on percentiles
start_line=$(echo "scale=0; ($total_lines * $START_PERCENTILE / 100) + 1" | bc)
end_line=$(echo "scale=0; $total_lines * $END_PERCENTILE / 100" | bc)

echo "Using tasks No. $start_line to $end_line (inclusive) out of 1-20 tasks"

# Create a temporary file with just the desired range
temp_file="tasks_${START_PERCENTILE}_${END_PERCENTILE}.md"
sed -n "${start_line},${end_line}p" tasks.md > "$temp_file"

while IFS= read -r task_name; do
    # Skip empty lines
    [ -z "$task_name" ] && continue

    # Remove any leading/trailing whitespace
    task_name=$(echo "$task_name" | xargs)

    echo "Processing task: $task_name..."

    # Check if trajectory file already exists
    if [ -f "$OUTPUTS_PATH/traj_${task_name}.json" ]; then
        echo "Skipping $task_name - trajectory file already exists"
        continue
    fi

    # Build the Python command
    COMMAND="poetry run python -m evaluation.benchmarks.paper_bench.run_infer \
            --agent-llm-config \"$AGENT_LLM_CONFIG\" \
            --outputs-path \"$OUTPUTS_PATH\" \
            --task-name \"$task_name\""

    # Add agent-config if it's defined
    if [ -n "$AGENT_CONFIG" ]; then
        COMMAND="$COMMAND --agent-config $AGENT_CONFIG"
    fi

    export PYTHONPATH=evaluation/benchmarks/paper_bench:$PYTHONPATH && \
        eval "$COMMAND"

done < "$temp_file"

rm "$temp_file"

echo "All inference completed successfully!"
