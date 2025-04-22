from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class CreatePlanObservation(Observation):
    """This data class represents the result of a plan creation."""

    observation: str = ObservationType.PLAN

    @property
    def message(self) -> str:
        return self.content
