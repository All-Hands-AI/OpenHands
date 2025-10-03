"""Utility functions for ACP server."""


def get_tool_kind(tool_name: str) -> str:
    """Map tool names to ACP ToolKind values."""
    tool_kind_mapping = {
        "execute_bash": "execute",
        "str_replace_editor": "edit",  # Can be read or edit depending on operation
        "browser_use": "fetch",
        "task_tracker": "think",
        "file_editor": "edit",
        "bash": "execute",
        "browser": "fetch",
    }
    return tool_kind_mapping.get(tool_name, "other")
