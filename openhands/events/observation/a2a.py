from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Literal

from openhands.a2a.common.types import Part, TaskArtifactUpdateEvent, TaskState, TaskStatusUpdateEvent, Task 
from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class A2AListRemoteAgentsObservation(Observation):
    """This data class represents the result of a MCP Server operation."""

    observation: str = ObservationType.A2A_LIST_REMOTE_AGENTS

    @property
    def message(self) -> str:
        return self.content
    
@dataclass
class A2ASendTaskUpdateObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""
    # id: str | None = None
    # final: bool = False
    # metadata: dict[str, Any] | None = None
    # task_state: TaskState | None = None
    # role: Literal["user", "agent"] | None = None
    # parts: List[Part] | None = None
    # timestamp: datetime | None = None
    task_update_event: TaskStatusUpdateEvent
    observation: str = ObservationType.A2A_SEND_TASK_UPDATE_EVENT

    @property
    def message(self) -> str:
        return self.content

@dataclass
class A2ASendTaskArtifactObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""
    # id: str = ''
    # name: str | None = None
    # description: str | None = None
    # index: int = 0
    # append: bool | None = None
    # lastChunk: bool | None = None
    # parts: List[Part] = field(default_factory=list, repr=False)
    # timestamp: datetime = field(default_factory=datetime.now, repr=False)
    # metadata: dict[str, Any] | None = None
    task_artifact_event: TaskArtifactUpdateEvent
    observation: str = ObservationType.A2A_SEND_TASK_ARTIFACT

    @property
    def message(self) -> str:
        return self.content
    
@dataclass
class A2ASendTaskResponseObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""

    task: Task
    # id: str
    # sessionId: str | None = None
    # final: bool = False
    # metadata: dict[str, Any] | None = None

    observation: str = ObservationType.A2A_SEND_TASK_RESPONSE

    @property
    def message(self) -> str:
        return self.content

