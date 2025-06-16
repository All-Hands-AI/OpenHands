# Devstral + Ollama System Prompt Fix

## Problem Description

When using Devstral models with Ollama, the model fails to behave as an agentic coding assistant and instead acts like a generic chat model. This happens because Ollama's Go template system doesn't apply the default system prompt that Devstral expects, unlike LMStudio which properly applies the Jinja template with a default system message.

### Root Cause

1. **LMStudio (Works Correctly)**: Uses Jinja templates that include a `default_system_message` when no system message is provided. This ensures Devstral gets its proper system prompt.

2. **Ollama (Broken)**: Uses Go templates that don't include a default system message mechanism. The template only applies system prompts if they're explicitly provided in the messages.

3. **Devstral Requirement**: Devstral is specifically trained to work as an agentic coding model and requires its specific system prompt to function correctly.

## Solution

This fix automatically detects when:
1. A Devstral model is being used (`devstral` in model name)
2. Ollama is the LLM provider (detected via `base_url` containing `:11434` or `ollama`, or `custom_llm_provider` containing `ollama`)
3. No proper Devstral system prompt is already present

When these conditions are met, it automatically injects the official Devstral system prompt.

## Implementation

### Files Added/Modified

1. **`openhands/llm/devstral_utils.py`** (New): Contains utility functions for detecting Devstral/Ollama usage and injecting the system prompt.

2. **`openhands/llm/llm.py`** (Modified): Integrated the fix into the LLM wrapper to automatically apply the system prompt when needed.

3. **`tests/unit/test_devstral_utils.py`** (New): Comprehensive tests for the utility functions.

### Key Functions

- `is_devstral_model(model_name)`: Detects if the model is a Devstral variant
- `is_ollama_provider(base_url, custom_llm_provider)`: Detects if Ollama is being used
- `needs_devstral_system_prompt_injection()`: Determines if injection is needed
- `ensure_devstral_system_prompt()`: Main function that applies the fix when needed

## Usage

The fix is automatic and transparent. Users don't need to change anything in their configuration. When using Devstral with Ollama, the system prompt will be automatically injected.

### Before the Fix
```
User: Create a button component
Devstral: I can help you with that. You should create the files yourself...
```

### After the Fix
```
User: Create a button component
Devstral: I'll create a button component for you. Let me start by exploring the project structure...
<function=execute_bash>
<parameter=command>find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | head -10</parameter>
</function>
```

## System Prompt Content

The injected system prompt is the official Devstral system prompt from the model repository, which includes:

- Role definition as an agentic coding assistant
- Efficiency guidelines for combining actions
- File system operation guidelines
- Code quality standards
- Version control best practices
- Problem-solving workflow
- Security considerations
- Environment setup instructions
- Troubleshooting guidelines

## Compatibility

- **LMStudio**: No impact (already works correctly)
- **Other providers**: No impact (only applies to Ollama + Devstral)
- **Non-Devstral models**: No impact (only applies to Devstral models)
- **Existing system prompts**: If a system prompt containing "Devstral" is already present, no injection occurs

## Testing

Run the tests to verify the fix:

```bash
poetry run pytest tests/unit/test_devstral_utils.py -v
```

All tests should pass, confirming that:
- Devstral models are correctly detected
- Ollama provider is correctly detected
- System prompt injection logic works correctly
- Existing functionality is preserved

## Future Considerations

This fix addresses the immediate compatibility issue between Devstral and Ollama. In the future, this could be enhanced by:

1. **Template Updates**: Working with the Ollama team to update the Devstral template to include a default system message
2. **Model-Specific Handling**: Extending this pattern to other models that might have similar requirements
3. **Configuration Options**: Adding user configuration to override the automatic injection behavior if needed

## References

- [GitHub Issue #8955](https://github.com/All-Hands-AI/OpenHands/issues/8955)
- [Devstral Model Repository](https://huggingface.co/mistralai/Devstral-Small-2505)
- [Devstral System Prompt](https://huggingface.co/mistralai/Devstral-Small-2505/blob/main/SYSTEM_PROMPT.txt)
- [Ollama Template Documentation](https://github.com/ollama/ollama/blob/main/docs/template.md)
- [Mistral Chat Templates Documentation](https://github.com/mistralai/cookbook/blob/main/concept-deep-dive/tokenization/chat_templates.md)
