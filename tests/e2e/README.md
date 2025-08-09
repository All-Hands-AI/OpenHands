# OpenHands End-to-End Tests

This directory contains end-to-end tests for the OpenHands application. These tests use Playwright to interact with the OpenHands UI and verify that the application works correctly.

## Running the Tests

### Prerequisites

- Python 3.12 or later
- Poetry
- Node.js
- Playwright

### Environment Variables

The following environment variables are required:

- `GITHUB_TOKEN`: A GitHub token with access to the repositories you want to test
- `LLM_MODEL`: The LLM model to use (e.g., "gpt-4o")
- `LLM_API_KEY`: The API key for the LLM model

Optional environment variables:

- `LLM_BASE_URL`: The base URL for the LLM API (if using a custom endpoint)

### Running Locally

To run the tests locally, you can use the provided script:

```bash
cd tests/e2e
./run_e2e_tests.sh
```

Or run the test directly:

```bash
cd tests/e2e
poetry run python -m pytest test_workflow.py::test_openhands_workflow -v --timeout=600
```

### GitHub Workflow

The tests can also be run as part of a GitHub workflow. The workflow is triggered by:

1. Adding the "end-to-end" label to a pull request
2. Manually triggering the workflow from the GitHub Actions tab

## Test Description

The end-to-end test performs the following steps:

1. Starts OpenHands according to the development workflow (using `make build; make run`)
2. Uses Playwright to manipulate the interface to:
   a. Click on the "All-Hands-AI/OpenHands" repo in the "Select a repo" dropdown
   b. Click "Launch"
   c. Check that the interface changes to the interface where we can control the agent
   d. Check that we go through the "Connecting", "Initializing Agent", and "Agent is waiting for user input..." states
   e. Enter "How many lines are there in the main README.md file?" and click the submit button
   f. Check that we go through the "Agent is running task" and "Agent has finished the task." states
   g. Check that the final agent message contains a number that matches "wc -l README.md"

## Troubleshooting

If the tests fail, check the following:

1. Make sure all required environment variables are set
2. Check the logs in `/tmp/openhands-e2e-test.log` and `/tmp/openhands-e2e-build.log`
3. Verify that the OpenHands application is running correctly
4. Check the Playwright test results in the `test-results` directory
