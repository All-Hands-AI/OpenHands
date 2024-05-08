from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from opendevin.core.schema import ActionType
from opendevin.events.observation import (
    AgentRecallObservation,
    NullObservation,
    Observation,
)

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController


class ChangeAgentStateAction(Action):
    """Fake action, just to notify the client that a task state has changed."""

    agent_state: str
    thought: str = ''
    action: ClassVar[str] = ActionType.CHANGE_AGENT_STATE

    @property
    def message(self) -> str:
        return f'Agent state changed to {self.agent_state}'


class AgentRecallAction(Action):
    query: str
    thought: str = ''
    action: ClassVar[str] = ActionType.RECALL

    async def run(self, controller: 'AgentController') -> AgentRecallObservation:
        return AgentRecallObservation(
            content='',
            memories=controller.agent.search_memory(self.query),
        )

    @property
    def message(self) -> str:
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."


class AgentSummarizeAction(Action):
    summary: str
    action: ClassVar[str] = ActionType.SUMMARIZE

    @property
    def message(self) -> str:
        return self.summary


class AgentFinishAction(Action):
    outputs: dict = Field(default_factory=dict)
    thought: str = ''
    action: ClassVar[str] = ActionType.FINISH

    @property
    def message(self) -> str:
        return "All done! What's next on the agenda?"


class AgentDelegateAction(Action):
    agent: str
    inputs: dict
    thought: str = ''
    action: ClassVar[str] = ActionType.DELEGATE

    async def run(self, controller: 'AgentController') -> Observation:
        await controller.start_delegate(self)
        return NullObservation('')

    @property
    def message(self) -> str:
        return f"I'm asking {self.agent} for help with this task."
