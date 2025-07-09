#!/usr/bin/env bash
set -eo pipefail
source "evaluation/utils/version_control.sh"

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --infer-dir DIR         Directory containing model inference outputs"
    echo "  --split SPLIT           SWE-Bench dataset split selection"
    echo "  --dataset DATASET       Dataset name"
    echo "  --max-infer-turn NUM    Max number of turns for coding agent"
    echo "  --align-with-max BOOL   Align failed instance indices with max iteration (true/false)"
    echo "  -h, --help              Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --infer-dir ./inference_outputs --split test --align-with-max false"
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
        --align-with-max)
            ALIGN_WITH_MAX="$2"
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

# Check for required arguments (only INFER_DIR is required)
if [ -z "$INFER_DIR" ]; then
    echo "Error: Missing required arguments (--infer-dir is required)"
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

if [ -z "$ALIGN_WITH_MAX" ]; then
    ALIGN_WITH_MAX="true"
    echo "Align with max not specified, using default: $ALIGN_WITH_MAX"
fi

# Validate align-with-max value
if [ "$ALIGN_WITH_MAX" != "true" ] && [ "$ALIGN_WITH_MAX" != "false" ]; then
    print_error "Invalid value for --align-with-max: $ALIGN_WITH_MAX. Must be 'true' or 'false'"
    exit 1
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

# Evaluation outputs
EVAL_DIR="$INFER_DIR/eval_outputs"

# Display configuration
print_header "Starting Localization Evaluation with the following configuration:"
echo "  Inference Directory:  $INFER_DIR"
if [ -d "$EVAL_DIR" ]; then
    echo "  Evaluation Directory:  $EVAL_DIR"
else
    echo "  Evaluation Directory:  None (evaluation outputs doesn't exist)"
fi
echo "  Output Directory:      $INFER_DIR/loc_eval"
echo "  Split:                 $SPLIT"
echo "  Dataset:               $DATASET"
echo "  Max Turns:             $MAX_TURN"
echo "  Align with Max:        $ALIGN_WITH_MAX"
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

# Create log directory if doesn't exists
mkdir -p "$INFER_DIR/loc_eval"

# Set up logging
LOG_FILE="$INFER_DIR/loc_eval/loc_evaluation_$(date +%Y%m%d_%H%M%S).log"
print_status "Logging output to: $LOG_FILE"

# Build the command
CMD_ARGS="\"$SCRIPT_NAME\" \
    --infer-dir \"$INFER_DIR\" \
    --split \"$SPLIT\" \
    --dataset \"$DATASET\" \
    --max-infer-turn \"$MAX_TURN\" \
    --align-with-max \"$ALIGN_WITH_MAX\""

# Run the Python script
print_header "Running localization evaluation..."
eval "$PYTHON_CMD $CMD_ARGS" 2>&1 | tee "$LOG_FILE"

# Check if the script ran successfully
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_status "Localization evaluation completed successfully!"
    print_status "Results saved to: $INFER_DIR/loc_eval"
    print_status "Log file: $LOG_FILE"

    # Display summary if results exist
    if [ -f "$INFER_DIR/loc_eval/loc_eval_results/loc_acc/overall_eval.json" ]; then
        print_header "Evaluation Summary:"
        cat "$INFER_DIR/loc_eval/loc_eval_results/loc_acc/overall_eval.json"
        echo
    fi
else
    print_error "Localization evaluation failed!"
    print_warning "Check the log file for details: $LOG_FILE"
    exit 1
fi
