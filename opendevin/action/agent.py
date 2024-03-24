from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import Action
if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AgentRecallAction(Action):
    query: str

    def run(self, controller: "AgentController") -> str:
        return controller.agent.search_memory(self.query)


@dataclass
class AgentThinkAction(Action):
    thought: str
    runnable: bool = False

    def run(self, controller: "AgentController") -> str:
        raise NotImplementedError


@dataclass
class AgentFinishAction(Action):
    runnable: bool = False

    def run(self, controller: "AgentController") -> str:
        raise NotImplementedError
