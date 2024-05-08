from typing import ClassVar, List

from opendevin.core.schema import ObservationType

from .observation import Observation


class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """

    memories: List[str]
    role: str = 'assistant'
    observation: ClassVar[str] = ObservationType.RECALL

    @property
    def message(self) -> str:
        return 'The agent recalled memories.'
