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
class AgentCondensationObservation(Observation):
    """The output of a condensation action."""

    observation: str = ObservationType.CONDENSE

    @property
    def message(self) -> str:
        return self.content


@dataclass
class AgentThinkObservation(Observation):
    """The output of a think action.

    In practice, this is a no-op, since it will just reply a static message to the agent
    acknowledging that the thought has been logged.
    """

    observation: str = ObservationType.THINK

    @property
    def message(self) -> str:
        return self.content
