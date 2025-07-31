#!/bin/bash

# Wrapper script to run the development setup tests with timing output
# Uses script command with awk to add timestamps to all output

echo "Starting timed development setup tests..."
echo "Output will include timestamps for all operations."
echo

# Check if script command is available
if ! command -v script &> /dev/null; then
    echo "Error: 'script' command not found. Please install it to run timed tests."
    exit 1
fi

# Run the main test script with timing
script -f -q >(awk '{ print strftime("[%H:%M:%S]"), $0 }') -c "./run-dev-setup-tests.sh"

echo
echo "Timed tests completed!"
