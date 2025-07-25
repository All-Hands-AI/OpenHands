"""
ReadOnlyAgent unified tools - inherits safe tools from CodeAct and adds read-only specific tools.
"""

# Import safe tools from CodeAct parent
from openhands.agenthub.codeact_agent.tools.unified import FinishTool

# Import our own read-only specific tools
from .grep_tool import GrepTool
from .view_tool import ViewTool
from .glob_tool import GlobTool

__all__ = [
    'FinishTool',  # Inherited from CodeAct
    'GrepTool',    # ReadOnly-specific
    'ViewTool',    # ReadOnly-specific  
    'GlobTool',    # ReadOnly-specific
]