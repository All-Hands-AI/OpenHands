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

# Create test-results directory if it doesn't exist
mkdir -p test-results

# Run the test with visible browser
echo "Running end-to-end tests with visible browser..."
cd "$(dirname "$0")"

# Check if the argument is a file or a test name
if [[ "$1" == *".py" ]]; then
  # It's a file, run the whole file
  echo "Running: pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 $1"
  poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 "$1"
elif [[ "$1" == "test_github_token_configuration" ]]; then
  # Run the GitHub token configuration test
  echo "Running: pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_github_token_configuration"
  poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_github_token_configuration
elif [[ "$1" == "test_conversation_start" ]]; then
  # Run the conversation start test
  echo "Running: pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_conversation_start"
  poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_conversation_start

elif [[ "$1" == "test_simple_browser_navigation" ]]; then
  # Run the simple browser navigation test
  echo "Running: pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_simple_browser_navigation"
  poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::test_simple_browser_navigation
else
  # It's a test name, run it from test_e2e_workflow.py
  echo "Running: pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::$1"
  poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 --timeout=600 test_e2e_workflow.py::$1
fi
