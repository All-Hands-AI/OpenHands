from dataclasses import dataclass, field
from typing import Any

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class TodoWriteObservation(Observation):
    """This data class represents the result of a todo write operation."""

    observation: str = ObservationType.TODO_WRITE
    todos: list[dict[str, Any]] = field(default_factory=list)
    """The updated list of todo items after the operation."""

    @property
    def message(self) -> str:
        return self.content
