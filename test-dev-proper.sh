#!/bin/bash

echo "=== DEV-PROPER SETUP TEST ==="
echo "Running full build setup: make build"

# Record start time
start_time=$(date +%s)

# Run the full build
make build

# Record end time
end_time=$(date +%s)
setup_duration=$((end_time - start_time))

echo "Setup completed in ${setup_duration} seconds"
echo "=== DEV-PROPER SETUP COMPLETE ==="
