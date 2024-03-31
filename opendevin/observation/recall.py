from dataclasses import dataclass
from typing import List

from .base import Observation

@dataclass
class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """

    memories: List[str]
    role: str = "assistant"
    observation : str = "recall"

    @property
    def message(self) -> str:
        return "The agent recalled memories."



