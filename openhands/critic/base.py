import abc

from pydantic import BaseModel

from openhands.events import Event


class CriticResult(BaseModel):
    """
    A critic result is a score and a message.
    """

    score: float

    def continue_execution(self) -> bool:
        """
        Whether to continue execution.
        """
        return self.score >= 0.5


class BaseCritic(abc.ABC):
    """
    A critic is a function that takes in a list of events and returns a score about the quality of those events.
    """

    @abc.abstractmethod
    def evaluate(self, events: list[Event]) -> CriticResult:
        pass
