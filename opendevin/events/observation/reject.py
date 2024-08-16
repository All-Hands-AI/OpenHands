from dataclasses import dataclass

from opendevin.core.schema import ObservationType

from .observation import Observation


@dataclass
class UserRejectObservation(Observation):
    """This data class represents the result of a successful action."""

    observation: str = ObservationType.USER_REJECTED

    @property
    def message(self) -> str:
        return self.content
