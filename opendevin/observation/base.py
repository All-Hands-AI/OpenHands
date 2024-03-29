import copy
from typing import List
from dataclasses import dataclass

@dataclass
class Observation:
    """
    This data class represents an observation of the environment.
    """

    content: str

    def __str__(self) -> str:
        return self.content

    def to_dict(self) -> dict:
        """Converts the observation to a dictionary."""
        extras = copy.deepcopy(self.__dict__)
        extras.pop("content", None)
        observation = "observation"
        if hasattr(self, "observation"):
            observation = self.observation
        return {
            "observation": observation,
            "content": self.content,
            "extras": extras,
            "message": self.message,
        }

    @property
    def message(self) -> str:
        """Returns a message describing the observation."""
        return ""


@dataclass
class NullObservation(Observation):
    """
    This data class represents a null observation.
    This is used when the produced action is NOT executable.
    """
    observation : str = "null"

    @property
    def message(self) -> str:
        return ""
