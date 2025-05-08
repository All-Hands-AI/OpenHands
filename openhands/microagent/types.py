from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig, MCPStdioServerConfig


class MicroagentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'
    REPO_KNOWLEDGE = 'repo'


class TriggerType(str, Enum):
    """Type of trigger for microagent activation."""

    ALWAYS = 'always'
    KEYWORD = 'keyword'


class MicroagentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    trigger_type: TriggerType = Field(default=TriggerType.KEYWORD)
    triggers: List[str] = []  # optional, only exists for knowledge microagents with keyword trigger_type
    mcp_tools: Optional[MCPConfig] = None  # optional, for microagents that provide additional MCP tools
