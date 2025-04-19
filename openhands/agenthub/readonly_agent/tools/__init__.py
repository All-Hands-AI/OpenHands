"""Tools for the ReadOnlyAgent.

This module defines the read-only tools for the ReadOnlyAgent.
"""

from .glob import GlobTool
from .grep import GrepTool
from .view import ViewTool

__all__ = [
    'ViewTool',
    'GrepTool',
    'GlobTool',
]

# Define the list of read-only tools
READ_ONLY_TOOLS = [
    ViewTool,
    GrepTool,
    GlobTool,
]
