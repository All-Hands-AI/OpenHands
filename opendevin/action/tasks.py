from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from opendevin.observation import NullObservation
from opendevin.schema import ActionType

from .base import ExecutableAction, NotExecutableAction

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AddTaskAction(ExecutableAction):
    parent: str
    goal: str
    subtasks: list = field(default_factory=list)
    thought: str = ''
    action: str = ActionType.ADD_TASK

    async def run(self, controller: 'AgentController') -> NullObservation:  # type: ignore
        if controller.state is not None:
            controller.state.plan.add_subtask(self.parent, self.goal, self.subtasks)
        return NullObservation('')

    @property
    def message(self) -> str:
        return f'Added task: {self.goal}'


@dataclass
class ModifyTaskAction(ExecutableAction):
    id: str
    state: str
    thought: str = ''
    action: str = ActionType.MODIFY_TASK

    async def run(self, controller: 'AgentController') -> NullObservation:  # type: ignore
        if controller.state is not None:
            controller.state.plan.set_subtask_state(self.id, self.state)
        return NullObservation('')

    @property
    def message(self) -> str:
        return f'Set task {self.id} to {self.state}'


@dataclass
class TaskStateChangedAction(NotExecutableAction):
    """Fake action, just to notify the client that a task state has changed."""
    task_state: str
    thought: str = ''
    action: str = ActionType.CHANGE_TASK_STATE

    @property
    def message(self) -> str:
        return f'Task state changed to {self.task_state}'
