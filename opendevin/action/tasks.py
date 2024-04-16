from dataclasses import dataclass, field

from .base import ExecutableAction
from opendevin.schema import ActionType
from opendevin.observation import NullObservation

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AddTaskAction(ExecutableAction):
    parent: str
    goal: str
    subtasks: list = field(default_factory=list)
    action: str = ActionType.ADD_TASK

    async def run(self, controller: 'AgentController') -> NullObservation:  # type: ignore
        controller.state.plan.add_subtask(self.parent, self.goal, self.subtasks)

    @property
    def message(self) -> str:
        return f'Added task: {self.goal}'


@dataclass
class ModifyTaskAction(ExecutableAction):
    id: str
    state: str
    action: str = ActionType.MODIFY_TASK

    async def run(self, controller: 'AgentController') -> NullObservation:  # type: ignore
        controller.state.plan.set_subtask_state(self.id, self.state)
        return NullObservation('')

    @property
    def message(self) -> str:
        return f'Set task {self.id} to {self.state}'
