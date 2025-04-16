from dataclasses import dataclass

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
class A2ASendTaskObservation(Observation):
    """This data class represents the result of a A2A Send Task operation."""

    observation: str = ObservationType.A2A_SEND_TASK

    @property
    def message(self) -> str:
        return self.content

