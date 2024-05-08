from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class AgentStateChangedObservation(Observation):
    """
    This data class represents the result from delegating to another agent
    """

    agent_state: str
    observation: ClassVar[str] = ObservationType.AGENT_STATE_CHANGED

    @property
    def message(self) -> str:
        return ''
