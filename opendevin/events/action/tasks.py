from dataclasses import dataclass, field

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class AddTaskAction(Action):
    parent: str
    goal: str
    subtasks: list = field(default_factory=list)
    thought: str = ''
    action: str = ActionType.ADD_TASK

    @property
    def message(self) -> str:
        return f'Added task: {self.goal}'


@dataclass
class ModifyTaskAction(Action):
    task_id: str
    state: str
    thought: str = ''
    action: str = ActionType.MODIFY_TASK

    @property
    def message(self) -> str:
        return f'Set task {self.task_id} to {self.state}'
