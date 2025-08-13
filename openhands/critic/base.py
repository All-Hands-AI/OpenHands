import abc

from pydantic import BaseModel

from openhands.events import Event


class CriticResult(BaseModel):
    """A critic result is a score and a message."""

    score: float
    message: str

    @property
    def success(self) -> bool:
        """Whether the agent is successful."""
        return self.score >= 0.5


class BaseCritic(abc.ABC):
    """A critic is a function that takes in a list of events, optional git patch, and returns a score about the quality of those events."""

    @abc.abstractmethod
    def evaluate(
        self, events: list[Event], git_patch: str | None = None
    ) -> CriticResult:
        pass
