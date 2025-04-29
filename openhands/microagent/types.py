from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class MicroagentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'
    REPO_KNOWLEDGE = 'repo'
    USER_INPUT_KNOWLEDGE = 'user_input_knowledge'  # Special type for microagents that require user input


class InputMetadata(BaseModel):
    """Metadata for task microagent inputs."""
    
    name: str
    description: str
    required: bool = False
    type: str = "string"
    validation: Optional[Dict[str, Any]] = None


class MicroagentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # optional, only exists for knowledge microagents
    inputs: List[InputMetadata] = []  # optional, only exists for task microagents
