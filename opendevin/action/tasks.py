from dataclasses import dataclass, field

from .base import NotExecutableAction
from opendevin.schema import ActionType


@dataclass
class AddTaskAction(NotExecutableAction):
    parent: str
    goal: str
    subtasks: list = field(default_factory=list)
    action: str = ActionType.ADD_TASK

    @property
    def message(self) -> str:
        return f"Added task: {self.goal}"


@dataclass
class ModifyTaskAction(NotExecutableAction):
    id: str
    state: str
    action: str = ActionType.MODIFY_TASK

    @property
    def message(self) -> str:
        return f"Set task {self.id} to {self.state}"
