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

### Configuration Options

The E2E tests support several command-line options:

- `--base-url`: Specify the base URL of the OpenHands instance under test (default: `http://localhost:12000`)
- `--headless`: Run browser in headless mode (default: `true`)
- `--no-headless`: Run browser in non-headless mode to watch the browser interactions
- `--slow-mo`: Add delay between actions in milliseconds (default: `0`)

### Running Locally

To run the full end-to-end test suite locally:

```bash
cd tests/e2e
poetry run pytest test_settings.py::test_github_token_configuration test_conversation.py::test_conversation_start -v
```

This runs all tests in sequence:
1. GitHub token configuration
2. Conversation start

#### Specifying a Custom Base URL

By default, the tests run against `http://localhost:12000`. You can specify a different OpenHands instance URL using the `--base-url` option:

```bash
cd tests/e2e
# Run against a remote instance
poetry run pytest test_settings.py::test_github_token_configuration test_conversation.py::test_conversation_start -v --base-url=https://my-openhands-instance.com

# Run against a CI instance
poetry run pytest test_settings.py::test_github_token_configuration test_conversation.py::test_conversation_start -v --base-url=http://ci-instance:8080

# Run against localhost with a different port
poetry run pytest test_settings.py::test_github_token_configuration test_conversation.py::test_conversation_start -v --base-url=http://localhost:3000
```

### Running Individual Tests

You can run individual tests directly:

```bash
cd tests/e2e
# Run the GitHub token configuration test
poetry run pytest test_settings.py::test_github_token_configuration -v

# Run the conversation start test
poetry run pytest test_conversation.py::test_conversation_start -v

# Run individual tests with custom base URL
poetry run pytest test_settings.py::test_github_token_configuration -v --base-url=https://my-instance.com

```

### Running with Visible Browser

To run the tests with a visible browser (non-headless mode) so you can watch the browser interactions:

```bash
cd tests/e2e
poetry run pytest test_settings.py::test_github_token_configuration -v --no-headless --slow-mo=50
poetry run pytest test_conversation.py::test_conversation_start -v --no-headless --slow-mo=50

# Combine with custom base URL
poetry run pytest test_settings.py::test_github_token_configuration -v --no-headless --slow-mo=50 --base-url=https://my-instance.com
```

### GitHub Workflow

The tests can also be run as part of a GitHub workflow. The workflow is triggered by:

1. Adding the "end-to-end" label to a pull request
2. Manually triggering the workflow from the GitHub Actions tab

## Test Descriptions

### GitHub Token Configuration Test

The GitHub token configuration test (`test_github_token_configuration`) performs the following steps:

1. Navigates to the OpenHands application
2. Checks if the GitHub token is already configured:
   - If not configured, it navigates to the settings page and configures it
   - If already configured, it verifies the repository selection is available
3. Verifies that the GitHub token is saved and the repository selection is available

### Conversation Start Test

The conversation start test (`test_conversation_start`) performs the following steps:

1. Navigates to the OpenHands application (assumes GitHub token is already configured)
2. Selects the "openhands-agent/OpenHands" repository
3. Clicks the "Launch" button
4. Waits for the conversation interface to load
5. Waits for the agent to initialize
6. Asks "How many lines are there in the main README.md file?"
7. Waits for and verifies the agent's response



### Simple Browser Navigation Test

A simple test (`test_simple_browser_navigation`) that just navigates to the OpenHands GitHub repository to verify the browser setup works correctly.

### Local Runtime Test

A separate test (`test_headless_mode_with_dummy_agent_no_browser` in `test_local_runtime.py`) that tests the local runtime with a dummy agent in headless mode.

## Troubleshooting

If the tests fail, check the following:

1. Make sure all required environment variables are set
2. Check the logs in `/tmp/openhands-e2e-test.log` and `/tmp/openhands-e2e-build.log`
3. Verify that the OpenHands application is running correctly
4. Check the Playwright test results in the `test-results` directory
