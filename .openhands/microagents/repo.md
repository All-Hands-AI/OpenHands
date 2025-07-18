This repository contains the code for OpenHands, an automated AI software engineer. It has a Python backend
(in the `openhands` directory) and React frontend (in the `frontend` directory).

## General Setup:
To set up the entire repo, including frontend and backend, run `make build`.
You don't need to do this unless the user asks you to, or if you're trying to run the entire application.

## Running OpenHands with OpenHands:
To run the full application to debug issues:
```bash
export INSTALL_DOCKER=0
export RUNTIME=local
make build && make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0 &> /tmp/openhands-log.txt &
```

IMPORTANT: Before making any changes to the codebase, ALWAYS run `make install-pre-commit-hooks` to ensure pre-commit hooks are properly installed.



Before pushing any changes, you MUST ensure that any lint errors or simple test errors have been fixed.

* If you've made changes to the backend, you should run `pre-commit run --config ./dev_config/python/.pre-commit-config.yaml` (this will run on staged files).
* If you've made changes to the frontend, you should run `cd frontend && npm run lint:fix && npm run build ; cd ..`
* If you've made changes to the VSCode extension, you should run `cd openhands/integrations/vscode && npm run lint:fix && npm run compile ; cd ../../..`

The pre-commit hooks MUST pass successfully before pushing any changes to the repository. This is a mandatory requirement to maintain code quality and consistency.

If either command fails, it may have automatically fixed some issues. You should fix any issues that weren't automatically fixed,
then re-run the command to ensure it passes. Common issues include:
- Mypy type errors
- Ruff formatting issues
- Trailing whitespace
- Missing newlines at end of files

## Repository Structure
Backend:
- Located in the `openhands` directory
- Testing:
  - All tests are in `tests/unit/test_*.py`
  - To test new code, run `poetry run pytest tests/unit/test_xxx.py` where `xxx` is the appropriate file for the current functionality
  - Write all tests with pytest

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
- Data Fetching & Cache Management:
  - We use TanStack Query (fka React Query) for data fetching and cache management
  - Data Access Layer: API client methods are located in `frontend/src/api` and should never be called directly from UI components - they must always be wrapped with TanStack Query
  - Custom hooks are located in `frontend/src/hooks/query/` and `frontend/src/hooks/mutation/`
  - Query hooks should follow the pattern use[Resource] (e.g., `useConversationMicroagents`)
  - Mutation hooks should follow the pattern use[Action] (e.g., `useDeleteConversation`)
  - Architecture rule: UI components → TanStack Query hooks → Data Access Layer (`frontend/src/api`) → API endpoints

VSCode Extension:
- Located in the `openhands/integrations/vscode` directory
- Setup: Run `npm install` in the extension directory
- Linting:
  - Run linting with fixes: `npm run lint:fix`
  - Check only: `npm run lint`
  - Type checking: `npm run typecheck`
- Building:
  - Compile TypeScript: `npm run compile`
  - Package extension: `npm run package-vsix`
- Testing:
  - Run tests: `npm run test`
- Development Best Practices:
  - Use `vscode.window.createOutputChannel()` for debug logging instead of `showErrorMessage()` popups
  - Pre-commit process runs both frontend and backend checks when committing extension changes

## Template for Github Pull Request

If you are starting a pull request (PR), please follow the template in `.github/pull_request_template.md`.

## Implementation Details

These details may or may not be useful for your current task.

### Microagents

Microagents are specialized prompts that enhance OpenHands with domain-specific knowledge and task-specific workflows. They are Markdown files that can include frontmatter for configuration.

#### Types:
- **Public Microagents**: Located in `microagents/`, available to all users
- **Repository Microagents**: Located in `.openhands/microagents/`, specific to this repository

#### Loading Behavior:
- **Without frontmatter**: Always loaded into LLM context
- **With triggers in frontmatter**: Only loaded when user's message matches the specified trigger keywords

#### Structure:
```yaml
---
triggers:
- keyword1
- keyword2
---
# Microagent Content
Your specialized knowledge and instructions here...
```

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

### Adding New LLM Models

To add a new LLM model to OpenHands, you need to update multiple files across both frontend and backend:

#### Model Configuration Procedure:

1. **Frontend Model Arrays** (`frontend/src/utils/verified-models.ts`):
   - Add the model to `VERIFIED_MODELS` array (main list of all verified models)
   - Add to provider-specific arrays based on the model's provider:
     - `VERIFIED_OPENAI_MODELS` for OpenAI models
     - `VERIFIED_ANTHROPIC_MODELS` for Anthropic models
     - `VERIFIED_MISTRAL_MODELS` for Mistral models
     - `VERIFIED_OPENHANDS_MODELS` for models available through OpenHands provider

2. **Backend CLI Integration** (`openhands/cli/utils.py`):
   - Add the model to the appropriate `VERIFIED_*_MODELS` arrays
   - This ensures the model appears in CLI model selection

3. **Backend Model List** (`openhands/utils/llm.py`):
   - **CRITICAL**: Add the model to the `openhands_models` list (lines 57-66) if using OpenHands provider
   - This is required for the model to appear in the frontend model selector
   - Format: `'openhands/model-name'` (e.g., `'openhands/o3'`)

4. **Backend LLM Configuration** (`openhands/llm/llm.py`):
   - Add to feature-specific arrays based on model capabilities:
     - `FUNCTION_CALLING_SUPPORTED_MODELS` if the model supports function calling
     - `REASONING_EFFORT_SUPPORTED_MODELS` if the model supports reasoning effort parameters
     - `CACHE_PROMPT_SUPPORTED_MODELS` if the model supports prompt caching
     - `MODELS_WITHOUT_STOP_WORDS` if the model doesn't support stop words

5. **Validation**:
   - Run backend linting: `pre-commit run --config ./dev_config/python/.pre-commit-config.yaml`
   - Run frontend linting: `cd frontend && npm run lint:fix`
   - Run frontend build: `cd frontend && npm run build`

#### Model Verification Arrays:

- **VERIFIED_MODELS**: Main array of all verified models shown in the UI
- **VERIFIED_OPENAI_MODELS**: OpenAI models (LiteLLM doesn't return provider prefix)
- **VERIFIED_ANTHROPIC_MODELS**: Anthropic models (LiteLLM doesn't return provider prefix)
- **VERIFIED_MISTRAL_MODELS**: Mistral models (LiteLLM doesn't return provider prefix)
- **VERIFIED_OPENHANDS_MODELS**: Models available through OpenHands managed provider

#### Model Feature Support Arrays:

- **FUNCTION_CALLING_SUPPORTED_MODELS**: Models that support structured function calling
- **REASONING_EFFORT_SUPPORTED_MODELS**: Models that support reasoning effort parameters (like o1, o3)
- **CACHE_PROMPT_SUPPORTED_MODELS**: Models that support prompt caching for efficiency
- **MODELS_WITHOUT_STOP_WORDS**: Models that don't support stop word parameters

#### Frontend Model Integration:

- Models are automatically available in the model selector UI once added to verified arrays
- The `extractModelAndProvider` utility automatically detects provider from model arrays
- Provider-specific models are grouped and prioritized in the UI selection

#### CLI Model Integration:

- Models appear in CLI provider selection based on the verified arrays
- The `organize_models_and_providers` function groups models by provider
- Default model selection prioritizes verified models for each provider
