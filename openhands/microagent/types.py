from enum import Enum
from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class MicroAgentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'
    REPO_KNOWLEDGE = 'repo'
    TASK = 'task'


class MCPServerConfig(TypedDict, total=False):
    """Type definition for MCP server configuration."""

    command: str
    args: list[str]
    env: dict[str, str] | None
    encoding: str
    encoding_error_handler: Literal['strict', 'ignore', 'replace']


class MicroAgentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroAgentType = Field(default=MicroAgentType.KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # optional, only exists for knowledge microagents
    mcp_configs: dict[
        str, MCPServerConfig
    ] = {}  # optional, map from server name to config


class TaskInput(BaseModel):
    """Input parameter for task-based agents."""

    name: str
    description: str
    required: bool = True
