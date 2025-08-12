from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class TaskTrackingObservation(Observation):
    """This data class represents the result of a task tracking operation."""

    observation: str = ObservationType.TASK_TRACKING

    @property
    def message(self) -> str:
        return self.content
