from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ErrorObservation(Observation):
    """This data class represents an error encountered by the agent.

    This is the type of error that LLM can recover from.
    E.g., Linter error after editing a file.
    """

    observation: str = ObservationType.ERROR

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        return f'**ErrorObservation**\n{self.content}'


@dataclass
class FatalErrorObservation(Observation):
    """This data class represents a fatal error encountered by the agent.

    This is the type of error that LLM CANNOT recover from, and the agent controller should stop the execution and report the error to the user.
    E.g., Remote runtime action execution failure: 503 Server Error: Service Unavailable for url OR 404 Not Found.
    """

    observation: str = ObservationType.ERROR

    def __str__(self) -> str:
        return f'**FatalErrorObservation**\n{self.content}'
