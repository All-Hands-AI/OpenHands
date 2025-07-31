from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


from dataclasses import dataclass, field

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ErrorObservation(Observation):
    """This data class represents an error encountered by the agent.

    This is the type of error that LLM can recover from.
    E.g., Linter error after editing a file.
    """

    observation: str = ObservationType.ERROR
    error_id: str = ''
    summary: str | None = field(default=None, metadata={'log_default': None})

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        if self.summary:
            return f'**ErrorObservation**\nSummary: {self.summary}\nContent: {self.content}'
        return f'**ErrorObservation**\n{self.content}'
