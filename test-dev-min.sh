#!/bin/bash

echo "=== DEV-MIN SETUP TEST ==="
echo "Running minimal setup: make install-pre-commit-hooks"

# Record start time
start_time=$(date +%s)

# Run the minimal setup
make install-pre-commit-hooks

# Record end time
end_time=$(date +%s)
setup_duration=$((end_time - start_time))

echo "Setup completed in ${setup_duration} seconds"
echo "=== DEV-MIN SETUP COMPLETE ==="
