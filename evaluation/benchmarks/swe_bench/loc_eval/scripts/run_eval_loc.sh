#!/usr/bin/env bash
set -eo pipefail
source "evaluation/utils/version_control.sh"

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --infer-dir DIR         Directory containing model inference outputs"
    echo "  --eval-dir DIR          Directory containing inference evaluation outputs (optional)"
    echo "  --save-dir DIR          Output directory to save eval results"
    echo "  --split SPLIT           SWE-Bench dataset split selection"
    echo "  --dataset DATASET       Dataset name"
    echo "  --max-infer-turn NUM    Max number of turns for coding agent"
    echo "  -h, --help              Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --infer-dir ./inference_outputs --eval-dir ./evaluation_outputs --save-dir ./saves --split test"
    echo "  $0 --infer-dir ./inference_outputs --save-dir ./saves --split test"
}

# Check if no arguments were provided
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --infer-dir)
            INFER_DIR="$2"
            shift 2
            ;;
        --eval-dir)
            EVAL_DIR="$2"
            shift 2
            ;;
        --save-dir)
            SAVE_DIR="$2"
            shift 2
            ;;
        --split)
            SPLIT="$2"
            shift 2
            ;;
        --dataset)
            DATASET="$2"
            shift 2
            ;;
        --max-infer-turn)
            MAX_TURN="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check for required arguments (only INFER_DIR and SAVE_DIR are required)
if [ -z "$INFER_DIR" ] || [ -z "$SAVE_DIR" ]; then
    echo "Error: Missing required arguments (--infer-dir and --save-dir are required)"
    usage
    exit 1
fi

# Set defaults for optional arguments if not provided
if [ -z "$SPLIT" ]; then
    SPLIT="test"
    echo "Split not specified, using default: $SPLIT"
fi

if [ -z "$DATASET" ]; then
    DATASET="princeton-nlp/SWE-bench_Verified"
    echo "Dataset not specified, using default: $DATASET"
fi

if [ -z "$MAX_TURN" ]; then
    MAX_TURN=20
    echo "Max inference turn not specified, using default: $MAX_TURN"
fi

# Handle optional EVAL_DIR
if [ -z "$EVAL_DIR" ] || [ "$EVAL_DIR" = "" ]; then
    echo "Evaluation directory not specified, script will run without it"
    EVAL_DIR_ARG=""
else
    EVAL_DIR_ARG="--eval-dir \"$EVAL_DIR\""
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[TASK]${NC} $1"
}

# Check if Python is available
print_header "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    else
        PYTHON_CMD="python"
        print_status "Using python command"
    fi
else
    PYTHON_CMD="python3"
    print_status "Using python3 command"
fi

# Check if the Python script exists
SCRIPT_NAME="./evaluation/benchmarks/swe_bench/loc_eval/loc_evaluator.py"
if [ ! -f "$SCRIPT_NAME" ]; then
    print_error "Python script '$SCRIPT_NAME' not found in current directory"
    print_warning "Make sure the Python script is in the same directory as this bash script"
    exit 1
fi

# Check if required directories exist
print_header "Validating directories..."
if [ ! -d "$INFER_DIR" ]; then
    print_error "Inference directory not found: $INFER_DIR"
    exit 1
fi

# Only check EVAL_DIR if it was provided and is not empty
if [ -n "$EVAL_DIR" ] && [ "$EVAL_DIR" != "" ] && [ ! -d "$EVAL_DIR" ]; then
    print_error "Evaluation directory not found: $EVAL_DIR"
    exit 1
fi

# Create output directory if it doesn't exist
if [ ! -d "$SAVE_DIR" ]; then
    print_status "Creating output directory: $SAVE_DIR"
    mkdir -p "$SAVE_DIR"
fi

# Display configuration
print_header "Starting Localization Evaluation with the following configuration:"
echo "  Inference Directory:   $INFER_DIR"
if [ -n "$EVAL_DIR" ] && [ "$EVAL_DIR" != "" ]; then
    echo "  Evaluation Directory:  $EVAL_DIR"
else
    echo "  Evaluation Directory:  (not provided)"
fi
echo "  Output Directory:      $SAVE_DIR"
echo "  Split:                 $SPLIT"
echo "  Dataset:               $DATASET"
echo "  Max Turns:             $MAX_TURN"
echo "  Python Command:        $PYTHON_CMD"
echo ""

# Check Python dependencies (optional check)
print_header "Checking Python dependencies..."
$PYTHON_CMD -c "
import sys
required_modules = ['pandas', 'json', 'os', 'argparse', 'collections']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f'Missing required modules: {missing_modules}')
    sys.exit(1)
else:
    print('All basic dependencies are available')
" || {
    print_error "Some Python dependencies are missing"
    print_warning "Please install required packages: pip install pandas"
    exit 1
}

# Set up logging
LOG_FILE="$SAVE_DIR/loc_evaluation_$(date +%Y%m%d_%H%M%S).log"
print_status "Logging output to: $LOG_FILE"

# Build the command with conditional eval-dir argument
CMD_ARGS="\"$SCRIPT_NAME\" \
    --infer-dir \"$INFER_DIR\" \
    --save-dir \"$SAVE_DIR\" \
    --split \"$SPLIT\" \
    --dataset \"$DATASET\" \
    --max-infer-turn \"$MAX_TURN\""

# Add eval-dir only if it's provided and not empty
if [ -n "$EVAL_DIR" ] && [ "$EVAL_DIR" != "" ]; then
    CMD_ARGS="$CMD_ARGS --eval-dir \"$EVAL_DIR\""
fi

# Run the Python script
print_header "Running localization evaluation..."
eval "$PYTHON_CMD $CMD_ARGS" 2>&1 | tee "$LOG_FILE"

# Check if the script ran successfully
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_status "Localization evaluation completed successfully!"
    print_status "Results saved to: $SAVE_DIR"
    print_status "Log file: $LOG_FILE"
    
    # Display summary if results exist
    if [ -f "$SAVE_DIR/loc_eval_results/loc_acc/overall_eval.json" ]; then
        print_header "Evaluation Summary:"
        cat "$SAVE_DIR/loc_eval_results/loc_acc/overall_eval.json"
        echo
    fi
else
    print_error "Localization evaluation failed!"
    print_warning "Check the log file for details: $LOG_FILE"
    exit 1
fi