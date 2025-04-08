"""Context reorganization tool for the CodeAct agent."""

from typing import Any, Dict, List, Optional

from openhands.events.action.context_reorganization import ContextReorganizationAction

__all__ = ['ContextReorganizeTool']


def ContextReorganizeTool(
    summary: str,
    files: Optional[List[Dict[str, Any]]] = None,
) -> ContextReorganizationAction:
    """Reorganize the context by providing a summary and optional files to include.

    This tool allows the agent to reorganize its context when it becomes too large,
    when prompted by the user, or when it contains redundant/outdated information.
    The tool will replace all previous context with a summary and the contents of
    the specified files.

    Args:
        summary: A structured summary of important information from the current conversation.
            This should include key insights, decisions, and context that should be preserved.
        files: A list of files to include in the context. Each file should be a dictionary
            with a 'path' key and an optional 'view_range' key. If 'view_range' is provided,
            only the specified lines will be included. Example:
            [
                {"path": "/workspace/main.py"},
                {"path": "/workspace/utils.py", "view_range": [10, 20]}
            ]

    Returns:
        ContextReorganizationAction: An action that will reorganize the context.
    """
    if files is None:
        files = []

    return ContextReorganizationAction(
        summary=summary,
        files=files,
    )
