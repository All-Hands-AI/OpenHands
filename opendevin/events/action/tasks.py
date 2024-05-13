from pydantic.dataclasses import Field, dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class AddTaskAction(Action):
    parent: str
    goal: str
    subtasks: list = Field(default_factory=list)
    thought: str = ''
    action: str = ActionType.ADD_TASK

    @property
    def message(self) -> str:
        return f'Added task: {self.goal}'


@dataclass
class ModifyTaskAction(Action):
    id: str
    state: str
    thought: str = ''
    action: str = ActionType.MODIFY_TASK

    @property
    def message(self) -> str:
        return f'Set task {self.id} to {self.state}'
