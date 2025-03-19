from enum import Enum

from pydantic import BaseModel, Field


class MicroAgentType(str, Enum):
    """Type of microagent."""

    KNOWLEDGE = 'knowledge'
    REPO_KNOWLEDGE = 'repo'
    TASK = 'task'


class MicroAgentMetadata(BaseModel):
    """Metadata for all microagents."""

    name: str = 'default'
    type: MicroAgentType = Field(default=MicroAgentType.KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # optional, only exists for knowledge microagents


class TaskInput(BaseModel):
    """Input parameter for task-based agents."""

    name: str
    description: str
    required: bool = True


class TaskStep(BaseModel):
    """A step in a task with completion status."""

    description: str
    completed: bool = False
    subtasks: list['TaskStep'] = []


class TaskProgress(BaseModel):
    """Progress tracking for a task."""

    title: str
    description: str
    steps: list[TaskStep] = []
    review_notes: str = ''
    completed: bool = False
