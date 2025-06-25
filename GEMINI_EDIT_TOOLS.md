# Gemini Edit Tools for OpenHands

This branch adds Gemini-style file editing tools to OpenHands. These tools are designed to be compatible with the Gemini CLI file editing tools, making it easier to port code between the two systems.

## Overview

The Gemini edit tools provide three main capabilities:

1. **replace** - A tool for replacing text within files with precise targeting
2. **write_file** - A tool for writing content to files
3. **read_file** - A tool for reading content from files with optional pagination

## Usage

To enable the Gemini edit tools, set the following configuration in your OpenHands config:

```toml
[agent]
enable_llm_editor = false  # Must be false to use Gemini edit tools
enable_editor = true       # Must be true to use any editor tools
enable_gemini_editor = true  # Enable Gemini-style edit tools
```

### Disabling the Previous Editing Tool

If you want to use only the Gemini-style editing tools and disable the previous editing tool (`str_replace_editor`), you have two options:

1. **Option 1**: Set `enable_editor = false` in your config. This will disable all editor tools except the LLM-based editor.

```toml
[agent]
enable_llm_editor = false
enable_editor = false  # Disables all editor tools
enable_gemini_editor = true  # This will have no effect since enable_editor is false
```

2. **Option 2**: Keep `enable_editor = true` but modify the agent's tool list to exclude the standard editor tool. This allows you to use the Gemini-style editing tools while disabling the standard editor tool.

```toml
[agent]
enable_llm_editor = false
enable_editor = true
enable_gemini_editor = true
```

Then, in your agent implementation, modify the tool list to exclude the standard editor tool and include only the Gemini-style editing tools.

## Tool Descriptions

### replace

The `replace` tool is designed to replace text within a file with precise targeting. It requires providing significant context around the change to ensure accurate replacements.

#### Parameters

- `file_path` - The absolute path to the file to modify
- `old_string` - The exact literal text to replace (including whitespace, indentation, etc.)
- `new_string` - The exact literal text to replace `old_string` with
- `expected_replacements` - (Optional) Number of replacements expected (defaults to 1)

#### Example

```json
{
  "file_path": "/path/to/file.py",
  "old_string": "def hello_world():\n    print('Hello, World!')\n    return None",
  "new_string": "def hello_world():\n    print('Hello, OpenHands!')\n    return True"
}
```

### write_file

The `write_file` tool is designed to write content to a file. If the file doesn't exist, it will be created. If it exists, it will be overwritten.

#### Parameters

- `file_path` - The absolute path to the file to write to
- `content` - The content to write to the file

#### Example

```json
{
  "file_path": "/path/to/file.py",
  "content": "def hello_world():\n    print('Hello, OpenHands!')\n    return True"
}
```

### read_file

The `read_file` tool is designed to read content from files. It supports pagination through large files using offset and limit parameters.

#### Parameters

- `absolute_path` - The absolute path to the file to read
- `offset` - (Optional) The 0-based line number to start reading from
- `limit` - (Optional) The maximum number of lines to read

#### Example

```json
{
  "absolute_path": "/path/to/file.py",
  "offset": 10,
  "limit": 20
}
```

## Implementation Details

The Gemini edit tools are implemented as follows:

1. **Tool Definitions** - The tool definitions are in `openhands/agenthub/codeact_agent/tools/gemini_edit_tool.py`
2. **Tool Handlers** - The tool handlers are in `openhands/runtime/plugins/agent_skills/gemini_file_editor/gemini_file_editor.py`
3. **Configuration** - The configuration option is in `openhands/core/config/agent_config.py`

## Differences from Standard OpenHands File Editing

The Gemini-style file editing tools differ from the standard OpenHands file editing tools in the following ways:

1. **Precise Targeting** - The `replace` tool requires providing significant context around the change to ensure accurate replacements.
2. **Multiple Replacements** - The `replace` tool can replace multiple occurrences of the same text when `expected_replacements` is specified.
3. **Simplified API** - The `write_file` tool provides a simplified API for writing content to files.

## Compatibility with Gemini CLI

These tools are designed to be compatible with the Gemini CLI file editing tools, making it easier to port code between the two systems. The tool names and parameters match those used in Gemini CLI.