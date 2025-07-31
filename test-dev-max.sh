#!/bin/bash

echo "=== DEV-MAX SETUP TEST ==="
echo "Running maximum setup: make install-full-pre-commit-hooks"

# Record start time
start_time=$(date +%s)

# Run the maximum setup
make build
make install-full-pre-commit-hooks

# Record end time
end_time=$(date +%s)
setup_duration=$((end_time - start_time))

echo "Setup completed in ${setup_duration} seconds"
echo "=== DEV-MAX SETUP COMPLETE ==="
