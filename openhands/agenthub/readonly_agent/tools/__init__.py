"""Tools for the ReadOnlyAgent.

This module imports the read-only tools from the CodeActAgent's tools module.
"""

from openhands.agenthub.codeact_agent.tools import (
    FinishTool,
    GlobTool,
    GrepTool,
    ThinkTool,
    ViewTool,
    WebReadTool,
)

# Define the list of read-only tools
READ_ONLY_TOOLS = [
    ThinkTool,
    ViewTool,
    GrepTool,
    GlobTool,
    FinishTool,
    WebReadTool,
]