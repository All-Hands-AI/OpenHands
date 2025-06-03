from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ReportVerificationObservation(Observation):
    """This data class represents the result from an agent asking for verification.

    Attributes:
        result (bool): The result of the verification.
        observation (ObservationType): The type of observation.
    """

    result: bool
    file_path: str | None = None
    observation: ObservationType = ObservationType.REPORT_VERIFICATION

    @property
    def message(self) -> str:
        return ''

    def __str__(self) -> str:
        return f'**ReportVerificationObservation**\n{self.result}\n{self.content}\n{self.file_path}'
