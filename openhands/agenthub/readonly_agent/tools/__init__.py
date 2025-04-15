"""Tools for the ReadOnlyAgent.

This module defines the read-only tools for the ReadOnlyAgent.
"""

from .finish import FinishTool
from .glob import GlobTool
from .grep import GrepTool
from .think import ThinkTool
from .view import ViewTool
from .web_read import WebReadTool

__all__ = [
    'FinishTool',
    'ViewTool',
    'ThinkTool',
    'GrepTool',
    'GlobTool',
    'WebReadTool',
]

# Define the list of read-only tools
READ_ONLY_TOOLS = [
    ThinkTool,
    ViewTool,
    GrepTool,
    GlobTool,
    FinishTool,
    WebReadTool,
]