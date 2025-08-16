"""
Gemini-optimized tools for OpenHands CodeActAgent.
These tools are designed to work better with Gemini models by providing
enhanced error handling, content correction, and more intuitive interfaces.
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import (
    GEMINI_READ_FILE_TOOL_NAME,
    GEMINI_REPLACE_TOOL_NAME,
    GEMINI_WRITE_FILE_TOOL_NAME,
)

# Detailed descriptions for Gemini tools
_GEMINI_READ_FILE_DESCRIPTION = """Enhanced file reading tool optimized for Gemini models.

Key features:
- Read files with optional line range support (offset and limit)
- Better error messages with suggestions for similar files
- Automatic handling of binary files and large files
- Directory listing when path points to a directory

Parameters:
- absolute_path: Absolute path to the file to read
- offset: Optional starting line number (1-based indexing)
- limit: Optional number of lines to read from offset

This tool provides more helpful error messages and suggestions compared to the standard file reader."""

_GEMINI_WRITE_FILE_DESCRIPTION = """Enhanced file writing tool optimized for Gemini models.

Key features:
- Write complete file content with automatic validation
- Create parent directories if they don't exist
- Content validation for common syntax issues
- Better error messages with actionable suggestions
- Automatic encoding handling

Parameters:
- file_path: Absolute path to the file to write
- content: Complete content to write to the file

This tool is ideal for creating new files or completely rewriting existing files.
For partial edits, use the gemini_replace tool instead."""

_GEMINI_REPLACE_DESCRIPTION = """Enhanced text replacement tool optimized for Gemini models.

Key features:
- Intelligent content correction when exact matches fail
- Better error messages with suggestions and similar content
- Support for expected replacement counts
- Automatic whitespace and formatting normalization
- Context expansion for better matching

Parameters:
- file_path: Absolute path to the file to edit
- old_string: Text to replace (more forgiving than standard str_replace)
- new_string: Replacement text
- expected_replacements: Number of replacements expected (default: 1)

This tool is much more forgiving than the standard str_replace tool and will attempt
to correct minor formatting differences automatically. It's designed to work better
with Gemini's natural language understanding capabilities."""


def create_gemini_read_file_tool() -> ChatCompletionToolParam:
    """Create the Gemini-optimized file reading tool."""
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_READ_FILE_TOOL_NAME,
            description=_GEMINI_READ_FILE_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'absolute_path': {
                        'description': 'Absolute path to the file to read (e.g., /workspace/file.py)',
                        'type': 'string',
                    },
                    'offset': {
                        'description': 'Optional starting line number (1-based). If specified, reading starts from this line.',
                        'type': 'integer',
                        'minimum': 1,
                    },
                    'limit': {
                        'description': 'Optional number of lines to read from the offset. If not specified, reads to end of file.',
                        'type': 'integer',
                        'minimum': 1,
                    },
                },
                'required': ['absolute_path'],
            },
        ),
    )


def create_gemini_write_file_tool() -> ChatCompletionToolParam:
    """Create the Gemini-optimized file writing tool."""
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_WRITE_FILE_TOOL_NAME,
            description=_GEMINI_WRITE_FILE_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': 'Absolute path to the file to write (e.g., /workspace/file.py)',
                        'type': 'string',
                    },
                    'content': {
                        'description': 'Complete content to write to the file',
                        'type': 'string',
                    },
                },
                'required': ['file_path', 'content'],
            },
        ),
    )


def create_gemini_replace_tool() -> ChatCompletionToolParam:
    """Create the Gemini-optimized text replacement tool."""
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_REPLACE_TOOL_NAME,
            description=_GEMINI_REPLACE_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': 'Absolute path to the file to edit (e.g., /workspace/file.py)',
                        'type': 'string',
                    },
                    'old_string': {
                        'description': 'Text to replace. This tool is more forgiving than str_replace and will attempt to correct minor formatting differences.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'Text to replace the old_string with',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'description': 'Number of replacements expected (default: 1). Use this when you want to replace multiple occurrences.',
                        'type': 'integer',
                        'minimum': 1,
                        'default': 1,
                    },
                },
                'required': ['file_path', 'old_string', 'new_string'],
            },
        ),
    )


# Tool collection for easy access
GEMINI_TOOLS = {
    GEMINI_READ_FILE_TOOL_NAME: create_gemini_read_file_tool,
    GEMINI_WRITE_FILE_TOOL_NAME: create_gemini_write_file_tool,
    GEMINI_REPLACE_TOOL_NAME: create_gemini_replace_tool,
}


def get_gemini_tools() -> list[ChatCompletionToolParam]:
    """Get all Gemini-optimized tools."""
    return [tool_func() for tool_func in GEMINI_TOOLS.values()]


def is_gemini_tool(tool_name: str) -> bool:
    """Check if a tool name is a Gemini-optimized tool."""
    return tool_name in GEMINI_TOOLS
