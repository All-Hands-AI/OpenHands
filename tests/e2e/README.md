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

To run the full end-to-end test suite locally, you can use the provided script:

```bash
cd tests/e2e
./run_e2e_tests.sh
```

This script runs the tests in sequence:
1. First, it runs the GitHub token configuration test
2. Then, it runs the conversation start test

### Running Individual Tests

You can run individual tests directly:

```bash
cd tests/e2e
# Run the GitHub token configuration test
poetry run pytest test_github_token_config.py -v

# Run the conversation start test
poetry run pytest test_conversation_start.py -v
```

### Running with Visible Browser

To run the tests with a visible browser (non-headless mode) so you can watch the browser interactions:

```bash
cd tests/e2e
./run_visible_browser_test.sh test_github_token_config
./run_visible_browser_test.sh test_conversation_start
```

You can also run a simple navigation test to verify your setup:

```bash
cd tests/e2e
./run_visible_browser_test.sh test_simple_browser_navigation
```

Or run the tests directly with pytest:

```bash
cd tests/e2e
poetry run pytest test_github_token_config.py -v --no-headless --slow-mo=50
poetry run pytest test_conversation_start.py -v --no-headless --slow-mo=50
```

### GitHub Workflow

The tests can also be run as part of a GitHub workflow. The workflow is triggered by:

1. Adding the "end-to-end" label to a pull request
2. Manually triggering the workflow from the GitHub Actions tab

## Test Descriptions

### GitHub Token Configuration Test

The GitHub token configuration test (`test_github_token_config.py`) performs the following steps:

1. Navigates to the OpenHands application
2. Checks if the GitHub token is already configured:
   - If not configured, it navigates to the settings page and configures it
   - If already configured, it verifies the repository selection is available
3. Verifies that the GitHub token is saved and the repository selection is available

### Conversation Start Test

The conversation start test (`test_conversation_start.py`) performs the following steps:

1. Navigates to the OpenHands application (assumes GitHub token is already configured)
2. Selects the "openhands-agent/OpenHands" repository
3. Clicks the "Launch" button
4. Waits for the conversation interface to load
5. Waits for the agent to initialize
6. Asks "How many lines are there in the main README.md file?"
7. Waits for and verifies the agent's response

### Simple Browser Navigation Test

A simple test (`test_simple_browser_navigation` in `test_workflow.py`) that just navigates to the OpenHands GitHub repository to verify the browser setup works correctly.

## Troubleshooting

If the tests fail, check the following:

1. Make sure all required environment variables are set
2. Check the logs in `/tmp/openhands-e2e-test.log` and `/tmp/openhands-e2e-build.log`
3. Verify that the OpenHands application is running correctly
4. Check the Playwright test results in the `test-results` directory
