from enum import Enum

from pydantic import BaseModel, Field

from openhands.core.config.mcp_config import (
    MCPConfig,
)


class MicroagentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'  # Optional microagent, triggered by keywords
    REPO_KNOWLEDGE = 'repo'  # Always active microagent
    TASK = 'task'  # Special type for task microagents that require user input


class InputMetadata(BaseModel):
    """Metadata for task microagent inputs."""

    name: str
    description: str


class MicroagentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # optional, only exists for knowledge microagents
    inputs: list[InputMetadata] = []  # optional, only exists for task microagents
    mcp_tools: MCPConfig | None = (
        None  # optional, for microagents that provide additional MCP tools
    )
