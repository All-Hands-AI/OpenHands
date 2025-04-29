from enum import Enum

from pydantic import BaseModel, Field


class MicroagentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'
    REPO_KNOWLEDGE = 'repo'
    USER_INPUT_KNOWLEDGE = 'user_input_knowledge'  # Special type for microagents that require user input


class MicroagentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # optional, only exists for knowledge microagents
