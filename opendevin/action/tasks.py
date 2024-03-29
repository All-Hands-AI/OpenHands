from dataclasses import dataclass, field

from .base import NotExecutableAction

@dataclass
class AddSubtaskAction(NotExecutableAction):
    parent: str
    goal: str
    subtasks: list = field(default_factory=list)

    @property
    def message(self) -> str:
        return f"Added subtask: {self.goal}"

@dataclass
class ModifySubtaskAction(NotExecutableAction):
    id: str
    state: str

    @property
    def message(self) -> str:
        return f"Set subtask {self.id} to {self.state}"

