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

# Run the tests in sequence with a visible browser
echo "Running end-to-end tests with visible browser..."

# Option 1: Run the full workflow test (all steps in one test)
echo "Running full workflow test..."
poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 test_e2e_workflow.py::test_full_workflow

# Check if the test passed
if [ $? -ne 0 ]; then
    echo "Full workflow test failed"
    echo "Please check the test output and screenshots in the test-results directory"
    exit 1
fi

echo "Full workflow test passed successfully!"

# Option 2: Run individual tests separately (uncomment to use)
# echo "Step 1: Running GitHub token configuration test..."
# poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 test_e2e_workflow.py::test_github_token_configuration
#
# # Check if the test passed
# if [ $? -ne 0 ]; then
#     echo "GitHub token configuration test failed"
#     echo "Please check the test output and screenshots in the test-results directory"
#     exit 1
# fi
#
# echo "GitHub token configuration test passed"
#
# # Step 2: Run the conversation start test
# echo "Step 2: Running conversation start test..."
# poetry run pytest -v --no-header --capture=no --no-headless --slow-mo=50 test_e2e_workflow.py::test_conversation_start
#
# # Check if the test passed
# if [ $? -ne 0 ]; then
#     echo "Conversation start test failed"
#     echo "Please check the test output and screenshots in the test-results directory"
#     exit 1
# fi
#
# echo "Conversation start test passed"
#
# echo "All end-to-end tests passed successfully!"
