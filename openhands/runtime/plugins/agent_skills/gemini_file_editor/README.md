# Gemini File Editor for OpenHands

This plugin implements Gemini-style file editing tools for OpenHands. It provides two main tools:

1. `replace` - A tool for replacing text within files with precise targeting
2. `write_file` - A tool for writing content to files

## Replace Tool

The `replace` tool is designed to replace text within a file with precise targeting. It requires providing significant context around the change to ensure accurate replacements.

### Parameters

- `file_path` - The absolute path to the file to modify
- `old_string` - The exact literal text to replace (including whitespace, indentation, etc.)
- `new_string` - The exact literal text to replace `old_string` with
- `expected_replacements` - (Optional) Number of replacements expected (defaults to 1)

### Example

```json
{
  "file_path": "/path/to/file.py",
  "old_string": "def hello_world():\n    print('Hello, World!')\n    return None",
  "new_string": "def hello_world():\n    print('Hello, OpenHands!')\n    return True"
}
```

## Write File Tool

The `write_file` tool is designed to write content to a file. If the file doesn't exist, it will be created. If it exists, it will be overwritten.

### Parameters

- `file_path` - The absolute path to the file to write to
- `content` - The content to write to the file

### Example

```json
{
  "file_path": "/path/to/file.py",
  "content": "def hello_world():\n    print('Hello, OpenHands!')\n    return True"
}
```

## Integration with OpenHands

This plugin is integrated with the OpenHands agent skills system and can be used by agents to perform file editing operations. The tools are registered with the following names:

- `replace` - For the replace tool
- `write_file` - For the write file tool

## Differences from Standard OpenHands File Editing

The Gemini-style file editing tools differ from the standard OpenHands file editing tools in the following ways:

1. **Precise Targeting** - The `replace` tool requires providing significant context around the change to ensure accurate replacements.
2. **Multiple Replacements** - The `replace` tool can replace multiple occurrences of the same text when `expected_replacements` is specified.
3. **Simplified API** - The `write_file` tool provides a simplified API for writing content to files.

These tools are designed to be compatible with the Gemini CLI file editing tools, making it easier to port code between the two systems.
