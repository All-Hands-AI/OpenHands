# Editor Configuration

OpenHands supports multiple file editing tools that can be enabled or disabled independently. This document explains how to configure these editors.

## Available Editors

OpenHands supports three types of file editing tools:

1. **Claude Editor** (`claude_editor`): The Claude-style string replace editor that requires exact string matching for replacements.
2. **Gemini Editor** (`replace`, `write_file`, `read_file`): The Gemini-style editing tools that provide more flexible file operations.
3. **LLM Editor** (`edit_file`): An LLM-based file editor that can edit files without requiring exact string matching.

## Configuration Options

In your agent configuration, you can enable or disable each editor independently:

```python
from openhands.core.config import AgentConfig

config = AgentConfig(
    # Master switch for all editors
    enable_editor=True,  # Set to False to disable all editors
    
    # Individual editor settings
    enable_claude_editor=True,  # Enable/disable Claude-style editor
    enable_gemini_editor=True,  # Enable/disable Gemini-style editors
    enable_llm_editor=False,    # Enable/disable LLM-based editor
)
```

### Default Configuration

By default:
- `enable_editor` is `True` (editors are enabled)
- `enable_claude_editor` is `True` (Claude editor is enabled)
- `enable_gemini_editor` is `False` (Gemini editors are disabled)
- `enable_llm_editor` is `False` (LLM editor is disabled)

### Legacy Behavior

For backward compatibility, if you don't specify `enable_claude_editor` and it's not defined in your configuration, the system will fall back to using the legacy `str_replace_editor` tool.

## Usage Examples

### Using Only Claude Editor

```python
config = AgentConfig(
    enable_claude_editor=True,
    enable_gemini_editor=False,
    enable_llm_editor=False,
)
```

### Using Only Gemini Editors

```python
config = AgentConfig(
    enable_claude_editor=False,
    enable_gemini_editor=True,
    enable_llm_editor=False,
)
```

### Using Both Claude and Gemini Editors

```python
config = AgentConfig(
    enable_claude_editor=True,
    enable_gemini_editor=True,
    enable_llm_editor=False,
)
```

### Using Only LLM Editor

```python
config = AgentConfig(
    enable_llm_editor=True,
)
```

### Disabling All Editors

```python
config = AgentConfig(
    enable_editor=False,
)
```

## Tool Names

When using these editors in your code, you can reference them by their tool names:

- Claude Editor: `claude_editor`
- Gemini Editors: `replace`, `write_file`, `read_file`
- LLM Editor: `edit_file`
- Legacy Editor: `str_replace_editor` (for backward compatibility)

## Migrating from Legacy Editor

If you're currently using the legacy `str_replace_editor` tool, you can migrate to the new Claude editor by updating your configuration to explicitly set `enable_claude_editor=True`. The Claude editor provides the same functionality as the legacy editor but with a more consistent naming convention.