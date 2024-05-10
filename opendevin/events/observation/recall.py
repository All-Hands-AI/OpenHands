from dataclasses import dataclass

from opendevin.core.schema import ObservationType

from .observation import Observation


@dataclass
class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """

    memories: list[str]
    role: str = 'assistant'
    observation: str = ObservationType.RECALL

    @property
    def message(self) -> str:
        return 'The agent recalled memories.'
