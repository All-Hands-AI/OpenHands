from dataclasses import dataclass

from opendevin.core.schema import ObservationType

from .observation import Observation


@dataclass
class AgentErrorObservation(Observation):
    """
    This data class represents an error encountered by the agent.
    """

    observation: str = ObservationType.ERROR

    @property
    def message(self) -> str:
        return 'Oops. Something went wrong: ' + self.content
