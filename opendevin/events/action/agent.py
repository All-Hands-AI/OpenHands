from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict

from opendevin.schema import ActionType

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.events.observation import (
        AgentMessageObservation,
        AgentRecallObservation,
        NullObservation,
        Observation,
    )


@dataclass
class AgentRecallAction(Action):
    query: str
    action: str = ActionType.RECALL

    async def run(self, controller: 'AgentController') -> 'AgentRecallObservation':
        return AgentRecallObservation(
            content='',
            memories=controller.agent.search_memory(self.query),
        )

    @property
    def message(self) -> str:
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."


@dataclass
class AgentThinkAction(Action):
    thought: str
    action: str = ActionType.THINK

    async def run(self, controller: 'AgentController') -> 'Observation':
        raise NotImplementedError

    @property
    def message(self) -> str:
        return self.thought


@dataclass
class AgentEchoAction(Action):
    content: str
    action: str = 'echo'

    async def run(self, controller: 'AgentController') -> 'Observation':
        return AgentMessageObservation(self.content)

    @property
    def message(self) -> str:
        return self.content


@dataclass
class AgentSummarizeAction(Action):
    summary: str
    action: str = ActionType.SUMMARIZE

    @property
    def message(self) -> str:
        return self.summary


@dataclass
class AgentFinishAction(Action):
    outputs: Dict = field(default_factory=dict)
    action: str = ActionType.FINISH

    async def run(self, controller: 'AgentController') -> 'Observation':
        raise NotImplementedError

    @property
    def message(self) -> str:
        return "All done! What's next on the agenda?"


@dataclass
class AgentDelegateAction(Action):
    agent: str
    inputs: dict
    action: str = ActionType.DELEGATE

    async def run(self, controller: 'AgentController') -> 'Observation':
        await controller.start_delegate(self)
        return NullObservation('')

    @property
    def message(self) -> str:
        return f"I'm asking {self.agent} for help with this task."
