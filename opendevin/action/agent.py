from dataclasses import dataclass, field
from typing import ClassVar

from opendevin.core.schema import ActionType

from .base import ExecutableAction, NotExecutableAction


@dataclass
class AgentRecallAction(ExecutableAction):
    query: str
    action: str = ActionType.RECALL
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."


@dataclass
class AgentSummarizeAction(Action):
    summary: str
    action: str = ActionType.SUMMARIZE

    @property
    def message(self) -> str:
        return self.summary


@dataclass
class AgentFinishAction(Action):
    outputs: dict = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.FINISH

    async def run(self, controller: 'AgentController') -> 'Observation':
        raise NotImplementedError

    @property
    def message(self) -> str:
        return "All done! What's next on the agenda?"


@dataclass
class AgentRejectAction(Action):
    outputs: dict = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.REJECT

    @property
    def message(self) -> str:
        return 'Task is rejected by the agent.'


@dataclass
class AgentDelegateAction(Action):
    agent: str
    inputs: dict
    action: str = ActionType.DELEGATE

    @property
    def message(self) -> str:
        return f"I'm asking {self.agent} for help with this task."
