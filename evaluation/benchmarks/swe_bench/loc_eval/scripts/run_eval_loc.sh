#!/bin/bash

# Config
INFER_DIR="./llm.claude-3-5-haiku1/litellm_proxy_claude-3-5-haiku-20241022"
EVAL_DIR="./evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/claude-3-5-haiku-20241022_maxiter_20_N_v0.38.0-no-hint-run_1/eval_outputs"
OUTPUT_DIR="./evaluation/benchmarks/swe_bench/loc_eval/eval_saves"
SPLIT="test"
DATASET="princeton-nlp/SWE-bench_Verified"
MAX_TURN=20

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -d, --infer-dir DIR      Directory containing model inference outputs"
    echo "                         (default: $INFER_DIR)"
    echo "  -d, --eval-dir DIR      Directory containing inference evaluation outputs"
    echo "                         (default: $EVAL_DIR)"
    echo "  -o, --output-dir DIR    Output directory to save eval results"
    echo "                         (default: $OUTPUT_DIR)"
    echo "  -s, --split SPLIT       SWE-Bench dataset split selection"
    echo "                         (default: $SPLIT)"
    echo "  --dataset DATASET       Dataset name"
    echo "                         (default: $DATASET)"
    echo "  --max-infer-turn NUM    Max number of turns for coding agent"
    echo "                         (default: $MAX_TURN)"
    echo "  -h, --help             Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --infer-dir ./my_data --output-dir ./my_output --split test"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--infer-dir)
            INFER_DIR="$2"
            shift 2
            ;;
        -d|--eval-dir)
            EVAL_DIR="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -s|--split)
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

if [ ! -d "$EVAL_DIR" ]; then
    print_error "Evaluation directory not found: $EVAL_DIR"
    exit 1
fi

# Create output directory if it doesn't exist
if [ ! -d "$OUTPUT_DIR" ]; then
    print_status "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Check for required subdirectories in data directory
if [ ! -d "$INFER_DIR/histories" ]; then
    print_error "Required subdirectory 'histories' not found in $INFER_DIR"
    exit 1
fi

if [ ! -d "$INFER_DIR/metrics" ]; then
    print_error "Required subdirectory 'metrics' not found in $INFER_DIR"
    exit 1
fi

# Display configuration
print_header "Starting Localization Evaluation with the following configuration:"
echo "  Inference Directory:   $INFER_DIR"
echo "  Evaluation Directory:   $EVAL_DIR"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Split:           $SPLIT"
echo "  Dataset:         $DATASET"
echo "  Max Turns:       $MAX_TURN"
echo "  Python Command:  $PYTHON_CMD"
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
LOG_FILE="$OUTPUT_DIR/loc_evaluation_$(date +%Y%m%d_%H%M%S).log"
print_status "Logging output to: $LOG_FILE"

# Run the Python script
print_header "Running localization evaluation..."
$PYTHON_CMD "$SCRIPT_NAME" \
    --infer-dir "$INFER_DIR" \
    --eval-dir "$EVAL_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --split "$SPLIT" \
    --dataset "$DATASET" \
    --max-infer-turn "$MAX_TURN" \
    2>&1 | tee "$LOG_FILE"

# Check if the script ran successfully
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_status "Localization evaluation completed successfully!"
    print_status "Results saved to: $OUTPUT_DIR"
    print_status "Log file: $LOG_FILE"
    
    # Display summary if results exist
    if [ -f "$OUTPUT_DIR/loc_eval_results/loc_acc/overall_eval.json" ]; then
        print_header "Evaluation Summary:"
        cat "$OUTPUT_DIR/loc_eval_results/loc_acc/overall_eval.json"
        echo
    fi
else
    print_error "Localization evaluation failed!"
    print_warning "Check the log file for details: $LOG_FILE"
    exit 1
fi