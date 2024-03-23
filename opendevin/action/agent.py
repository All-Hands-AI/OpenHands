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

    def run(self, controller: "AgentController") -> str:
        return self.thought


@dataclass
class AgentFinishAction(Action):

    def run(self, controller: "AgentController") -> str:
        return "finish"
