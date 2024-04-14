from dataclasses import dataclass
from typing import List

from .base import Observation
from opendevin.schema import ObservationType


@dataclass
class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """

    memories: List[str]
    role: str = "assistant"
    observation: str = ObservationType.RECALL

    @property
    def message(self) -> str:
        return "The agent recalled memories."
