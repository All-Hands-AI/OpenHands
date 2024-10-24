"""This file contains a global singleton of the `EditTool` class as well as raw functions that expose its __call__."""

from .base import CLIResult, ToolError, ToolResult
from .impl import Command, EditTool

_GLOBAL_EDITOR = EditTool()


def _make_api_tool_result(
    result: ToolResult,
) -> str:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: str = ''
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        assert result.output, 'Expecting output in file_editor'
        tool_result_content = _maybe_prepend_system_tool_result(result, result.output)
        assert (
            not result.base64_image
        ), 'Not expecting base64_image as output in file_editor'
    if is_error:
        return f'ERROR:\n{tool_result_content}'
    else:
        return tool_result_content


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str) -> str:
    if result.system:
        result_text = f'<system>{result.system}</system>\n{result_text}'
    return result_text


def file_editor(
    command: Command,
    path: str,
    file_text: str | None = None,
    view_range: list[int] | None = None,
    old_str: str | None = None,
    new_str: str | None = None,
    insert_line: int | None = None,
) -> str:
    try:
        result: CLIResult = _GLOBAL_EDITOR(
            command=command,
            path=path,
            file_text=file_text,
            view_range=view_range,
            old_str=old_str,
            new_str=new_str,
            insert_line=insert_line,
        )
    except ToolError as e:
        return _make_api_tool_result(ToolResult(error=e.message))
    return _make_api_tool_result(result)


__all__ = ['file_editor']
