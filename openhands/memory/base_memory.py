from abc import ABC, abstractmethod
from typing import Any


class Memory(ABC):
    """Abstract base class for all memory modules."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the memory module to a dictionary of individual memories."""
        pass

    # @abstractmethod
    # def from_dict(self, data: dict[str, Any]) -> None:
    #    """Load the memory module from a dictionary of individual memories."""
    #    pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the memory module."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the memory module."""
        pass
