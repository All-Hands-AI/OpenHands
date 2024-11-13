from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class AgentDelegateObservation(Observation):
    """This data class represents the result from delegating to another agent.

    Attributes:
        content (str): The content of the observation.
        outputs (dict): The outputs of the delegated agent.
        observation (str): The type of observation.
    """

    outputs: dict
    observation: str = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return ""
