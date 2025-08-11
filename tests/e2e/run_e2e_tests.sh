#!/bin/bash
set -e

# Set environment variables
export INSTALL_DOCKER=0
export RUNTIME=local
export FRONTEND_PORT=12000
export FRONTEND_HOST=0.0.0.0
export BACKEND_HOST=0.0.0.0

# Check for required environment variables and set defaults if needed
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Warning: GITHUB_TOKEN not set, using default value for testing"
  export GITHUB_TOKEN="test-token"
fi

if [ -z "$LLM_MODEL" ]; then
  echo "Warning: LLM_MODEL not set, using default value for testing"
  export LLM_MODEL="gpt-4o"
fi

if [ -z "$LLM_API_KEY" ]; then
  echo "Warning: LLM_API_KEY not set, using default value for testing"
  export LLM_API_KEY="test-key"
fi

# Check if OpenHands is running
if ! nc -z localhost 12000; then
  echo "Error: OpenHands is not running on port 12000"
  echo "Please start OpenHands with 'make build && make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0' before running the tests"
  exit 1
fi

# Run the test
echo "Running end-to-end tests..."
poetry run python -m pytest test_workflow.py::test_openhands_workflow -v
