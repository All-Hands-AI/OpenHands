# System Prompt Filename Configuration Feature

## Overview

This feature adds the ability to configure a custom system prompt filename in the `AgentConfig`, making the system prompt configurable instead of being hardcoded to `system_prompt.j2` in the agent's prompt directory.

## Implementation Summary

### 1. AgentConfig Enhancement

**File**: `openhands/core/config/agent_config.py`

```python
system_prompt_filename: str = Field(default="system_prompt.j2")
"""Filename of the system prompt template file within the agent's prompt directory. Defaults to 'system_prompt.j2'."""
```

### 2. PromptManager Enhancement

**File**: `openhands/utils/prompt.py`

- Added `system_prompt_filename` parameter to `__init__` method with default `"system_prompt.j2"`
- Updated `_load_system_template()` method to use the specified filename
- Leverages existing `_load_template()` method for consistency
- Handles filenames with or without `.j2` extension

### 3. CodeActAgent Integration

**File**: `openhands/agenthub/codeact_agent/codeact_agent.py`

```python
self._prompt_manager = PromptManager(
    prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
    system_prompt_filename=self.config.system_prompt_filename,
)
```

## Usage Examples

### 1. Default Behavior (Backward Compatible)

```python
# Uses default "system_prompt.j2"
config = AgentConfig()
```

### 2. Custom System Prompt

```python
# Uses custom filename within the agent's prompt directory
config = AgentConfig(system_prompt_filename="specialized_prompt.j2")
```

### 3. TOML Configuration

```toml
[agent]
system_prompt_filename = "custom_prompt.j2"
enable_browsing = true

[agent.CodeReviewAgent]
system_prompt_filename = "code_review_prompt.j2"
enable_browsing = false
```

### 4. Creating Custom Prompts

Place your custom prompt file in the agent's prompt directory:

```
openhands/agenthub/codeact_agent/prompts/
├── system_prompt.j2          # Default
├── code_review_prompt.j2     # Custom for code review
├── debugging_prompt.j2       # Custom for debugging
└── ...
```

## Benefits

1. **Simplicity**: Uses filenames instead of absolute paths
2. **Consistency**: Works within existing prompt directory structure
3. **Flexibility**: Different agent configurations can use different prompts
4. **Backward Compatibility**: Default behavior unchanged
5. **Maintainability**: Custom prompts are organized with agent code

## Key Improvements Over Path-Based Approach

- **Cleaner Configuration**: No need to specify full paths
- **Better Organization**: Prompts stay within agent directories
- **Easier Deployment**: No absolute path dependencies
- **Simpler Implementation**: Leverages existing template loading logic

## Testing

Comprehensive tests verify:
- Default behavior with `"system_prompt.j2"`
- Custom filename functionality
- Serialization/deserialization
- TOML configuration parsing
- Error handling for missing files

## Backward Compatibility

✅ **Fully backward compatible**
- Existing configurations work without changes
- Default behavior unchanged
- No breaking changes to existing APIs

## Future Enhancements

This foundation enables:
- Template inheritance and composition
- Dynamic prompt selection based on task type
- Prompt versioning and A/B testing
- Agent specialization frameworks
