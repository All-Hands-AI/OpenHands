"""llm_integration.py

This module shows how to integrate the file operation tools with the main LLM class.
"""

from openhands.llm.llm import LLM
from openhands.runtime.plugins.agent_skills.file_ops.llm_tools import (
    get_tool_functions,
    get_tool_schemas,
)


def register_file_tools(llm: LLM) -> None:
    """Registers file operation tools with an LLM instance.

    Args:
        llm: The LLM instance to register tools with
    """

    tool_schemas = get_tool_schemas()
    tool_functions = get_tool_functions()

    llm.register_functions(tool_schemas, tool_functions)


def get_file_tools_prompt() -> str:
    """Returns a system prompt that describes the available file tools."""

    return """
You can perform file operations using the following functions:

1. open_file(path, line_number=1, context_lines=100)
   - Opens and reads a file, showing content around the specified line
   - Returns the file content as a string

2. search_file(search_term, file_path=None)
   - Searches for a term in a specific file or the currently open file
   - Returns search results as a string

3. search_dir(search_term, dir_path='./')
   - Searches for a term in all files in a directory
   - Returns search results as a string

4. find_file(file_name, dir_path='./')
   - Finds all files with a given name in a directory
   - Returns list of matching files as a string

Call these functions by name with the required parameters when you need to perform file operations.
"""
