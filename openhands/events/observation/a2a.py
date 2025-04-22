from dataclasses import dataclass

from openhands.a2a.common.types import (
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)
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

    agent_name: str
    task_update_event: TaskStatusUpdateEvent
    observation: str = ObservationType.A2A_SEND_TASK_UPDATE_EVENT

    @property
    def message(self) -> str:
        return self.content


@dataclass
class A2ASendTaskArtifactObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""

    agent_name: str
    task_artifact_event: TaskArtifactUpdateEvent
    observation: str = ObservationType.A2A_SEND_TASK_ARTIFACT

    @property
    def message(self) -> str:
        return self.content


@dataclass
class A2ASendTaskResponseObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""

    agent_name: str
    task: Task
    observation: str = ObservationType.A2A_SEND_TASK_RESPONSE

    @property
    def message(self) -> str:
        return self.content
