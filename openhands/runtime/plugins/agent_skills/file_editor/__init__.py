"""This file contains a global singleton of the `EditTool` class as well as raw functions that expose its __call__."""

from .base import CLIResult, ToolResult
from .impl import Command, EditTool

_GLOBAL_EDITOR = EditTool()


def _make_api_tool_result(
    result: ToolResult,
) -> dict:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[dict] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        assert isinstance(tool_result_content, list)
        if result.output:
            tool_result_content.append(
                {
                    'type': 'text',
                    'text': _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/png',
                        'data': result.base64_image,
                    },
                }
            )
    return {
        'content': tool_result_content,
        'is_error': is_error,
    }


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
):
    result: CLIResult = _GLOBAL_EDITOR(
        command=command,
        path=path,
        file_text=file_text,
        view_range=view_range,
        old_str=old_str,
        new_str=new_str,
        insert_line=insert_line,
    )
    return _make_api_tool_result(result)


__all__ = ['file_editor']
