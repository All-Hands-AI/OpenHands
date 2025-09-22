# OpenHands CLI Directory Separation and Bash Tool Fix

## Summary of Changes

This document summarizes the fixes implemented to address the issues with WORK_DIR and CONFIGURATIONS_DIR separation, and the bash tool spec configuration in the OpenHands CLI.

## Issues Fixed

### 1. WORK_DIR and CONFIGURATIONS_DIR Separation

**Problem**: Previously, both the working directory for agent operations and the configuration storage used the same directory (`~/.openhands`), which caused confusion and potential conflicts.

**Solution**: Separated the directories into two distinct purposes:
- `CONFIGURATIONS_DIR`: `~/.openhands` - Used for storing agent settings and CLI configuration files
- `WORK_DIR`: `os.getcwd()` - The current working directory where the CLI is executed, used for agent operations

### 2. Bash Tool Spec Dynamic Working Directory

**Problem**: When loading agent specifications from storage, the BashTool would use a hardcoded working directory path instead of the current directory where the CLI is being run.

**Solution**: Modified the AgentStore to dynamically update the BashTool's `working_dir` parameter to use the current working directory when loading agent specifications.

## Files Modified

### 1. `openhands_cli/locations.py`
- Separated `WORKING_DIR` into `CONFIGURATIONS_DIR` and `WORK_DIR`
- `CONFIGURATIONS_DIR` = `~/.openhands` (for storing settings)
- `WORK_DIR` = `os.getcwd()` (current directory for operations)

### 2. `openhands_cli/tui/settings/store.py`
- Updated `AgentStore` to use `CONFIGURATIONS_DIR` for file storage
- Added logic in `load()` method to fix BashTool working_dir parameter
- When loading agents, BashTool specs are updated to use current directory

### 3. `openhands_cli/tui/settings/settings_screen.py`
- Updated imports to use both `CONFIGURATIONS_DIR` and `WORK_DIR`
- Changed file storage to use `CONFIGURATIONS_DIR`
- Updated agent creation to use `WORK_DIR` for working directory
- Fixed configuration file path display

## New Tests Added

Created comprehensive test suite in `tests/test_directory_separation.py` with 10 test cases:

### TestDirectorySeparation
- `test_work_dir_and_configurations_dir_are_different`: Verifies directories are separate
- `test_agent_store_uses_configurations_dir`: Confirms AgentStore uses config directory
- `test_agent_store_initialization`: Tests proper initialization

### TestBashToolSpecFix
- `test_bash_tool_spec_updated_on_load`: Verifies BashTool working_dir is updated
- `test_non_bash_tools_unchanged_on_load`: Ensures other tools remain unchanged
- `test_agent_without_tools_loads_correctly`: Tests agents with empty tools
- `test_agent_with_empty_tools_loads_correctly`: Tests agents with empty tools list
- `test_bash_tool_without_params_gets_working_dir`: Tests BashTool without params

### TestIntegration
- `test_agent_creation_uses_work_dir_for_tools`: Integration test for agent creation
- `test_configurations_stored_separately_from_work_dir`: Verifies separation works

## Behavior Changes

### Before the Fix
1. Both agent operations and configuration storage used `~/.openhands`
2. BashTool would use whatever working directory was saved in the agent spec
3. No clear separation between operational and configuration concerns

### After the Fix
1. Configuration files are stored in `~/.openhands` (CONFIGURATIONS_DIR)
2. Agent operations use the current working directory (WORK_DIR)
3. BashTool always uses the current directory, regardless of saved spec
4. Clear separation of concerns between storage and operations

## Testing

All existing tests continue to pass (53 original tests + 10 new tests = 63 total tests passing).

The new tests specifically verify:
- Directory separation works correctly
- BashTool specs are properly updated on load
- Configuration storage is separate from working directory
- Integration between components works as expected

## Impact

These changes ensure that:
1. The OpenHands CLI works correctly regardless of where it's executed
2. Agent operations happen in the user's current directory
3. Configuration is consistently stored in the user's home directory
4. The bash tool always operates in the correct context (current directory)
5. No breaking changes to existing functionality