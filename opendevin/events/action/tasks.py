from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from opendevin.core.schema import ActionType
from opendevin.events.observation import NullObservation

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AddTaskAction(Action):
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
class ModifyTaskAction(Action):
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
