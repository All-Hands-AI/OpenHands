This repository contains the code for OpenHands, an automated AI software engineer. It has a Python backend
(in the `openhands` directory) and React frontend (in the `frontend` directory).

## General Setup:

IMPORTANT: Before making any changes to the codebase, ALWAYS run `make install-pre-commit-hooks` to ensure pre-commit hooks are properly installed.

Before pushing any changes, you MUST ensure that any lint errors or simple test errors have been fixed.

* If you've made changes to the backend, you should run `pre-commit run --config ./dev_config/python/.pre-commit-config.yaml` (this will run on staged files).
* If you've made changes to the frontend, you should run `cd frontend && npm run lint:fix && npm run build ; cd ..`

The pre-commit hooks MUST pass successfully before pushing any changes to the repository. This is a mandatory requirement to maintain code quality and consistency.

If either command fails, it may have automatically fixed some issues. You should fix any issues that weren't automatically fixed,
then re-run the command to ensure it passes. Common issues include:
- Mypy type errors
- Ruff formatting issues
- Trailing whitespace
- Missing newlines at end of files

## Testing and Debugging

### Environment Setup for Testing
- Run `make build` to install all dependencies (only necessary for running tests):
  ```bash
  make build
  ```
  **IMPORTANT**: When using `execute_bash` to run `make build` or similar long-running commands, set the `timeout` parameter to a high value (e.g., 600 seconds):
  ```
  execute_bash(command="make build", timeout=600)
  ```

#### Docker Installation
**NOTE: Docker installation is ONLY required for running runtime tests with the Docker runtime.**

- Install Docker on Debian-based systems:
  ```bash
  sudo apt-get update
  sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
  curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io
  ```
- Start Docker daemon (in container environments without systemd):
  ```bash
  sudo dockerd > /tmp/docker.log 2>&1 & sleep 5
  ```
- Verify Docker installation:
  ```bash
  sudo docker run hello-world
  ```

#### Development Environment Setup
- Before running `make run`, ensure netcat is installed:
  ```bash
  sudo apt-get install -y netcat-openbsd
  ```

### Unit Tests
- All unit tests are in `tests/unit/test_*.py`
- To test new code, run `poetry run pytest tests/unit/test_xxx.py` where `xxx` is the appropriate file for the current functionality
- Write all tests with pytest

### Runtime Tests
- Runtime tests are in `tests/runtime/test_*.py`
- Run tests with different runtime implementations by setting the `TEST_RUNTIME` environment variable:
  ```bash
  # Use Docker runtime (default)
  DEBUG=1 poetry run pytest -vvxss tests/runtime/test_bash.py
  
  # Use CLI runtime (more reliable in some environments)
  DEBUG=1 TEST_RUNTIME=cli poetry run pytest -vvxss tests/runtime/test_bash.py
  
  # Run a specific test
  DEBUG=1 TEST_RUNTIME=cli poetry run pytest -vvxss tests/runtime/test_bash.py::test_bash_server
  ```
- **IMPORTANT**: Runtime tests can take a long time to run, especially when building Docker images. Set a high timeout value:
  ```
  execute_bash(command="DEBUG=1 poetry run pytest -vvxss tests/runtime/test_bash.py", timeout=600)
  ```
- The `DEBUG=1` flag enables more verbose logging
- The `-vvxss` flags make the test output more verbose and stop after the first failure

### Debugging Docker Issues
- Check Docker container status:
  ```bash
  sudo docker ps -a
  ```
- View Docker logs:
  ```bash
  sudo docker logs <container_id>
  ```
- Check Docker daemon logs:
  ```bash
  sudo cat /tmp/docker.log | tail -n 100
  ```
- Check OpenHands logs:
  ```bash
  cat logs/openhands_*.log | grep -i error | tail -n 20
  ```

## Repository Structure
Backend:
- Located in the `openhands` directory

Frontend:
- Located in the `frontend` directory
- Prerequisites: A recent version of NodeJS / NPM
- Setup: Run `npm install` in the frontend directory
- Testing:
  - Run tests: `npm run test`
  - To run specific tests: `npm run test -- -t "TestName"`
  - Our test framework is vitest
- Building:
  - Build for production: `npm run build`
- Environment Variables:
  - Set in `frontend/.env` or as environment variables
  - Available variables: VITE_BACKEND_HOST, VITE_USE_TLS, VITE_INSECURE_SKIP_VERIFY, VITE_FRONTEND_PORT
- Internationalization:
  - Generate i18n declaration file: `npm run make-i18n`


## Template for Github Pull Request

If you are starting a pull request (PR), please follow the template in `.github/pull_request_template.md`.

## Runtime Architecture
- OpenHands uses a Docker-based runtime for secure execution of agent actions
- The runtime builds a custom Docker image based on a specified base image
- The image includes OpenHands-specific code and the runtime client
- The runtime client executes actions in the sandboxed environment and returns observations
- More details in the [runtime architecture documentation](https://docs.all-hands.dev/usage/architecture/runtime)

## Implementation Details

These details may or may not be useful for your current task.

### Frontend

#### Action Handling:
- Actions are defined in `frontend/src/types/action-type.ts`
- The `HANDLED_ACTIONS` array in `frontend/src/state/chat-slice.ts` determines which actions are displayed as collapsible UI elements
- To add a new action type to the UI:
  1. Add the action type to the `HANDLED_ACTIONS` array
  2. Implement the action handling in `addAssistantAction` function in chat-slice.ts
  3. Add a translation key in the format `ACTION_MESSAGE$ACTION_NAME` to the i18n files
- Actions with `thought` property are displayed in the UI based on their action type:
  - Regular actions (like "run", "edit") display the thought as a separate message
  - Special actions (like "think") are displayed as collapsible elements only

#### Adding User Settings:
- To add a new user setting to OpenHands, follow these steps:
  1. Add the setting to the frontend:
     - Add the setting to the `Settings` type in `frontend/src/types/settings.ts`
     - Add the setting to the `ApiSettings` type in the same file
     - Add the setting with an appropriate default value to `DEFAULT_SETTINGS` in `frontend/src/services/settings.ts`
     - Update the `useSettings` hook in `frontend/src/hooks/query/use-settings.ts` to map the API response
     - Update the `useSaveSettings` hook in `frontend/src/hooks/mutation/use-save-settings.ts` to include the setting in API requests
     - Add UI components (like toggle switches) in the appropriate settings screen (e.g., `frontend/src/routes/app-settings.tsx`)
     - Add i18n translations for the setting name and any tooltips in `frontend/src/i18n/translation.json`
     - Add the translation key to `frontend/src/i18n/declaration.ts`
  2. Add the setting to the backend:
     - Add the setting to the `Settings` model in `openhands/storage/data_models/settings.py`
     - Update any relevant backend code to apply the setting (e.g., in session creation)