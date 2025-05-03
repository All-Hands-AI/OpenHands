from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class AgentDelegateObservation(Observation):
    """This data class represents the result from delegating to another agent.

    Attributes:
        content (str): The content of the observation.
        outputs (dict): The outputs of the delegated agent. (deprecated)
        observation (str): The type of observation.
    """

    outputs: dict
    """Deprecated.
    Delegate agents run similarly to the main agent:
    - start from a prompt (passed in the 'prompt' field)
    - end with an AgentFinishAction.
    """
    observation: str = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return self.content
