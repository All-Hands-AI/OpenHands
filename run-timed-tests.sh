#!/bin/bash

# Wrapper script to run the development setup tests with timing output
# Redirects verbose output to log files and shows file paths

echo "Starting timed development setup tests..."
echo "Verbose output will be redirected to log files."
echo

# Create logs directory if it doesn't exist
LOGS_DIR="build/test-logs"
mkdir -p "$LOGS_DIR"

# Generate timestamp for this run
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Define log file paths
MAIN_LOG="$LOGS_DIR/main_test_${TIMESTAMP}.log"
SETUP_LOG="$LOGS_DIR/setup_output_${TIMESTAMP}.log"
COMMIT_LOG="$LOGS_DIR/commit_output_${TIMESTAMP}.log"

echo "Log files for this run:"
echo "  Main test log: $MAIN_LOG"
echo "  Setup output: $SETUP_LOG"
echo "  Commit output: $COMMIT_LOG"
echo

# Check if script command is available
if ! command -v script &> /dev/null; then
    echo "Error: 'script' command not found. Please install it to run timed tests."
    exit 1
fi

# Export log file paths so the main script can use them
export SETUP_LOG_FILE="$PWD/$SETUP_LOG"
export COMMIT_LOG_FILE="$PWD/$COMMIT_LOG"

# Run the main test script with timing, redirecting main output to log
echo "Running tests... (check log files for detailed output)"
script -f -q >(awk '{ print strftime("[%H:%M:%S]"), $0 }') -c "./run-dev-setup-tests.sh" > "$MAIN_LOG" 2>&1

# Show the final report from the main log
echo
echo "=== EXTRACTING FINAL REPORT ==="
if grep -A 20 "=== FINAL TEST REPORT ===" "$MAIN_LOG"; then
    echo
else
    echo "Could not extract final report. Check $MAIN_LOG for full details."
fi

echo
echo "Timed tests completed!"
echo
echo "Log files created:"
echo "  Main test log: $MAIN_LOG"
echo "  Setup output: $SETUP_LOG"
echo "  Commit output: $COMMIT_LOG"
echo
echo "Use 'cat <filename>' or 'less <filename>' to view the logs."
