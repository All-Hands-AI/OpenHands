"""OpenHands Tools Module

This module provides a unified interface for AI agent tools, encapsulating:
- Tool definitions and schemas
- Parameter validation
- Action creation from function calls
- Error handling and interpretation
- Response processing

This decouples tool logic from agent processing, making it easier to add new tools
or modify existing ones.
"""

from .base import Tool, ToolError, ToolValidationError
from .bash_tool import BashTool
from .file_editor_tool import FileEditorTool
from .registry import ToolRegistry

__all__ = [
    'Tool',
    'ToolError',
    'ToolValidationError',
    'BashTool',
    'FileEditorTool',
    'ToolRegistry',
]