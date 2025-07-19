"""Unified tool architecture for LocAgent.

LocAgent extends CodeActAgent with specialized search and exploration tools.
It inherits all CodeAct tools and adds its own search capabilities.
"""

# Import parent tools from CodeAct
from openhands.agenthub.codeact_agent.tools.unified import (
    BashTool,
    BrowserTool,
    FileEditorTool,
    FinishTool,
)

# Import LocAgent-specific tools
from .explore_structure_tool import ExploreStructureTool
from .search_entity_tool import SearchEntityTool
from .search_repo_tool import SearchRepoTool

__all__ = [
    # Inherited from CodeAct
    'BashTool',
    'BrowserTool', 
    'FileEditorTool',
    'FinishTool',
    # LocAgent-specific
    'ExploreStructureTool',
    'SearchEntityTool',
    'SearchRepoTool',
]