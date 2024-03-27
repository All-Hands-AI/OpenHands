from dataclasses import dataclass

from .base import NotExecutableAction

@dataclass
class AddSubtaskAction(NotExecutableAction):
    parent: str
    goal: str

    @property
    def message(self) -> str:
        return f"Added subtask: {self.goal}"

@dataclass
class CloseSubtaskAction(NotExecutableAction):
    id: str
    completed: bool

    @property
    def message(self) -> str:
        return f"Closed subtask {self.id}"

