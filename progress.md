# OpenHands Configuration Enhancement Progress

## Overview
Adding user-configurable LLM parameters and agent settings to the OpenHands frontend settings UI.

## Completed Work ✅

### Temperature Configuration
- ✅ **Backend**: Updated `Settings` model to include `temperature: float = Field(default=0.0)`
- ✅ **Backend**: Added temperature to `from_config()` method in Settings model
- ✅ **Backend**: Added temperature merging logic in `store_llm_settings()`
- ✅ **Backend**: Ensured temperature always has default value (0.0) in API responses
- ✅ **Frontend**: Added `TEMPERATURE: number` to Settings type
- ✅ **Frontend**: Added temperature input field in advanced settings UI
- ✅ **Frontend**: Added form handling for temperature in both basic and advanced modes
- ✅ **Frontend**: Added translation key `SETTINGS$TEMPERATURE_HELP` with multi-language support
- ✅ **Frontend**: Fixed unlocalized string check by using translation key
- ✅ **Tests**: All existing tests pass
- ✅ **Build**: Frontend builds successfully without TypeScript errors
- ✅ **Validation**: MyPy checks pass

## Current Work In Progress 🚧

### Additional LLM Parameters - COMPLETED ✅
All LLM configuration fields have been successfully added following the temperature implementation pattern:

#### Completed Fields:
1. ✅ **top_p** (float, default: 1.0)
2. ✅ **max_output_tokens** (int | None, default: None)
3. ✅ **max_input_tokens** (int | None, default: None)
4. ✅ **max_message_chars** (int, default: 30,000)
5. ✅ **input_cost_per_token** (float | None, default: None)
6. ✅ **output_cost_per_token** (float | None, default: None)

#### Implementation Steps Completed:
- ✅ **Backend**: Updated `Settings` model in `/openhands/storage/data_models/settings.py`
- ✅ **Backend**: Added fields to `from_config()` method to map from LLMConfig
- ✅ **Backend**: Added field handling in settings route response
- ✅ **Frontend**: Added fields to `Settings` and `ApiSettings` types
- ✅ **Frontend**: Added fields to settings mapping hooks
- ✅ **Frontend**: Added fields to DEFAULT_SETTINGS
- ✅ **Frontend**: Added translation keys for labels and help text
- ✅ **Frontend**: Regenerated i18n declarations
- ✅ **Frontend**: Added input fields in advanced settings UI
- ✅ **Frontend**: Added form handling and dirty state tracking
- ✅ **Tests**: All backend unit tests pass
- ✅ **Build**: Frontend builds successfully without TypeScript errors
- ✅ **Validation**: Unlocalized strings check passes after fixing input name exclusion
- ✅ **Final Verification**: All backend tests pass and frontend builds successfully without errors

## Summary ✅
**All LLM configuration parameters have been successfully implemented!**

The implementation includes complete backend and frontend support for:
- `temperature` (previously implemented)
- `top_p`
- `max_output_tokens`
- `max_input_tokens`
- `max_message_chars`
- `input_cost_per_token`
- `output_cost_per_token`

All fields follow consistent patterns for:
- Type safety with proper defaults
- Backend-frontend data mapping
- Form handling and validation
- Internationalization support
- Build validation and testing

## Planned Work 📋

### Additional LLM Configuration Parameters (Phase 2)
Based on analysis of `config.template.toml` and `LLMConfig`, the following LLM parameters could be made configurable:

#### Advanced LLM Parameters:
1. **timeout** (int | None, default: None) - API timeout in seconds
2. **num_retries** (int, default: 4) - Number of retry attempts for failed LLM calls
3. **retry_min_wait** (int, default: 5) - Minimum wait time between retries (seconds)
4. **retry_max_wait** (int, default: 30) - Maximum wait time between retries (seconds)
5. **retry_multiplier** (float, default: 2.0) - Exponential backoff multiplier
6. **disable_vision** (bool | None, default: None) - Disable image processing for cost reduction
7. **caching_prompt** (bool, default: true) - Enable prompt caching if supported
8. **drop_params** (bool, default: true) - Drop unmapped parameters without exception
9. **modify_params** (bool, default: true) - Allow liteLLM to modify parameters
10. **native_tool_calling** (bool | None, default: None) - Use native tool calling if supported
11. **reasoning_effort** (str | None, default: "high") - Reasoning effort for o1 models (low/medium/high)
12. **seed** (int | None, default: None) - Random seed for reproducible outputs
13. **top_k** (float | None, default: None) - Top-k sampling parameter
14. **custom_llm_provider** (str | None, default: None) - Custom LLM provider
15. **custom_tokenizer** (str | None, default: None) - Custom tokenizer for token counting

### Core Configuration Parameters (Phase 3)
Settings from the `[core]` section that could be user-configurable:

#### Session & Performance:
1. **max_iterations** (int, default: 500) - Maximum number of agent iterations
2. **max_budget_per_task** (float, default: 0.0) - Maximum budget per task (0.0 = no limit)
3. **reasoning_effort** (str, default: "medium") - Global reasoning effort setting
4. **debug** (bool, default: false) - Enable debug mode
5. **enable_default_condenser** (bool, default: true) - Enable default LLM summarizing condenser

#### File Handling:
1. **file_uploads_max_file_size_mb** (int, default: 0) - Maximum file upload size in MB
2. **file_uploads_restrict_file_types** (bool, default: false) - Restrict file upload types
3. **file_uploads_allowed_extensions** (list[str], default: [".*"]) - Allowed file extensions

#### Data & Persistence:
1. **save_trajectory_path** (str | None, default: None) - Path to save conversation trajectories
2. **save_screenshots_in_trajectory** (bool, default: false) - Include screenshots in trajectories
3. **max_concurrent_conversations** (int, default: 3) - Max concurrent conversations per user
4. **conversation_max_age_seconds** (int, default: 864000) - Auto-close conversations after time

### Agent Configuration Parameters (Phase 4)
Settings from the `[agent]` section that should be configurable:

#### Agent Capabilities (already planned):
1. **enable_browsing** (bool, default: true) - Enable web browsing capability
2. **enable_llm_editor** (bool, default: false) - Enable LLM-based draft editor
3. **enable_editor** (bool, default: true) - Enable standard str_replace_editor
4. **enable_jupyter** (bool, default: true) - Enable IPython/Jupyter tools
5. **enable_cmd** (bool, default: true) - Enable command execution
6. **enable_think** (bool, default: true) - Enable thinking/reasoning step
7. **enable_finish** (bool, default: true) - Enable task completion
8. **enable_prompt_extensions** (bool, default: true) - Enable microagent and repo info
9. **disabled_microagents** (list[str], default: []) - List of microagents to disable
10. **enable_history_truncation** (bool, default: true) - Truncate history at context limit

### Sandbox Configuration Parameters (Phase 5)
Settings from the `[sandbox]` section for advanced users:

#### Container & Runtime:
1. **sandbox_timeout** (int, default: 120) - Sandbox timeout in seconds
2. **base_container_image** (str, default: "nikolaik/python-nodejs:python3.12-nodejs22") - Base container image
3. **use_host_network** (bool, default: false) - Use host network for sandbox
4. **enable_auto_lint** (bool, default: false) - Enable automatic linting after edits
5. **initialize_plugins** (bool, default: true) - Initialize sandbox plugins
6. **keep_runtime_alive** (bool, default: false) - Keep runtime alive after session ends
7. **close_delay** (int, default: 300) - Delay before closing idle runtimes (seconds)
8. **enable_gpu** (bool, default: false) - Enable GPU support in runtime

### Security Configuration Parameters (Phase 6)
Settings from the `[security]` section:

1. **confirmation_mode** (bool, default: false) - Require confirmation for dangerous actions
2. **enable_security_analyzer** (bool, default: false) - Enable security analysis of code
3. **security_analyzer** (str | None, default: None) - Security analyzer to use

### Implementation Priority & Phases:

**Phase 1 (COMPLETED)**: Core LLM parameters (temperature, top_p, etc.)

**Phase 2 (Next Priority)**: Advanced LLM parameters
- Most impactful for power users and cost optimization
- Retry settings for reliability
- Vision and caching settings for performance/cost

**Phase 3**: Core session settings
- Affects user experience and safety limits
- Budget and iteration controls

**Phase 4**: Agent capabilities
- Core functionality toggles
- Already partially planned

**Phase 5**: Sandbox settings
- Advanced configuration for power users
- Infrastructure-level settings

**Phase 6**: Security settings
- Important but typically set once

### UI Organization:
- **Basic Settings**: Core LLM (model, key, temperature, top_p)
- **Advanced LLM**: Advanced LLM parameters (retry, caching, vision, etc.)
- **Agent Settings**: Agent capabilities and behavior
- **Session Settings**: Iterations, budget, file handling
- **Sandbox Settings**: Container and runtime configuration (admin-level)
- **Security Settings**: Confirmation mode and security analysis

## Notes
- Following the same pattern established with temperature implementation
- Maintaining backward compatibility with existing configurations
- Ensuring proper validation and error handling
- All fields properly internationalized with translation support
- Type safety maintained throughout frontend and backend

## ✅ Final Status - All Core Tasks Completed Successfully

### Phase 1: LLM Parameters ✅ COMPLETE
All core LLM configuration parameters successfully implemented with full stack support.

### Phase 2: Agent Capabilities ✅ COMPLETE
**Agent Settings UI and backend integration fully implemented!**

**Key Achievements:**
- ✅ Complete Agent Settings page with intuitive UI organization
- ✅ Full backend support for all 10 agent capability parameters
- ✅ Proper navigation integration at /settings/agent
- ✅ Form validation, dirty state tracking, and save functionality
- ✅ Comprehensive internationalization for all UI elements
- ✅ All TypeScript compilation and backend tests passing
- ✅ No unlocalized strings or translation gaps
- ✅ Updated mock handlers for consistent testing

**Agent Capabilities Implemented:**
1. **Tool Capabilities**: enable_browsing, enable_jupyter, enable_cmd
2. **Editor Settings**: enable_llm_editor, enable_editor
3. **Agent Behavior**: enable_think, enable_finish, enable_prompt_extensions, enable_history_truncation
4. **Microagent Management**: disabled_microagents (comma-separated list)

**Technical Implementation:**
- Backend: Settings model, API routes, config mapping
- Frontend: React components, hooks, types, validation
- UI/UX: Organized sections, help text, consistent styling
- Testing: Mock data, unit tests, build verification
- I18n: Complete translation coverage for 15+ languages

The OpenHands frontend now provides comprehensive user-configurable settings for both LLM parameters and agent capabilities, following established patterns and maintaining high code quality standards.
