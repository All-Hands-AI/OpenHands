#!/bin/bash
#
# Script to run patch localization analysis for SWE-bench evaluation outputs
#
# Usage:
#   ./run_localization_analysis.sh <eval_output_dir> [options]
#
# Examples:
#   # Analyze all instances
#   ./run_localization_analysis.sh /path/to/eval_outputs
#
#   # Analyze with limit (for testing)
#   ./run_localization_analysis.sh /path/to/eval_outputs --limit 10
#
#   # Specify output file
#   ./run_localization_analysis.sh /path/to/eval_outputs --output /path/to/results.json
#
#   # Use different dataset
#   ./run_localization_analysis.sh /path/to/eval_outputs --dataset princeton-nlp/SWE-bench_Lite

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to the Python script
PYTHON_SCRIPT="${SCRIPT_DIR}/analyze_patch_localization.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <eval_output_dir> [options]"
    echo ""
    echo "Required:"
    echo "  eval_output_dir    Path to evaluation output directory"
    echo ""
    echo "Options:"
    echo "  --dataset NAME     Dataset name (default: princeton-nlp/SWE-bench_Verified)"
    echo "  --split SPLIT      Dataset split (default: test)"
    echo "  --output FILE      Output JSON file path"
    echo "  --limit N          Limit number of instances to analyze"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/eval_outputs"
    echo "  $0 /path/to/eval_outputs --limit 10"
    echo "  $0 /path/to/eval_outputs --output results.json"
    exit 1
fi

# Check if evaluation output directory exists
EVAL_OUTPUT_DIR="$1"
if [ ! -d "$EVAL_OUTPUT_DIR" ]; then
    echo "Error: Directory not found: $EVAL_OUTPUT_DIR"
    exit 1
fi

# Check for required Python packages
echo "Checking dependencies..."
python3 -c "import datasets" 2>/dev/null || {
    echo "Error: 'datasets' package not found. Please install it with:"
    echo "  pip install datasets"
    exit 1
}

# Run the analysis
echo "Starting patch localization analysis..."
echo "Evaluation output directory: $EVAL_OUTPUT_DIR"
echo ""

python3 "$PYTHON_SCRIPT" "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✓ Analysis completed successfully!"
else
    echo ""
    echo "✗ Analysis failed with exit code $exit_code"
    exit $exit_code
fi
