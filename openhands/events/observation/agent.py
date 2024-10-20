from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class AgentStateChangedObservation(Observation):
    """This data class represents the result from delegating to another agent"""

    agent_state: str
    observation: str = ObservationType.AGENT_STATE_CHANGED

    @property
    def message(self) -> str:
        return ''


@dataclass
class AgentRecallObservation(Observation):
    query: str
    memory: str
    observation: str = ObservationType.AGENT_RECALL

    @property
    def message(self) -> str:
        return f'Memory:\n{self.memory}'
