#!/bin/bash

echo "=== OPENHANDS AGENT SETUP TEST ==="
echo "Running OpenHands agent setup: .openhands/setup.sh"

# Record start time
start_time=$(date +%s)

# Run the OpenHands agent setup
bash .openhands/setup.sh

# Record end time
end_time=$(date +%s)
setup_duration=$((end_time - start_time))

echo "Setup completed in ${setup_duration} seconds"
echo "=== OPENHANDS AGENT SETUP COMPLETE ==="
