from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import Action, Executable, NotExecutable
if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AgentRecallAction(Action, Executable):
    query: str

    def run(self, controller: "AgentController") -> str:
        return controller.agent.search_memory(self.query)


@dataclass
class AgentThinkAction(Action, Executable):
    thought: str
    runnable: bool = False

    def run(self, controller: "AgentController") -> str:
        raise NotImplementedError


@dataclass
class AgentFinishAction(Action, Executable):
    runnable: bool = False

    def run(self, controller: "AgentController") -> str:
        raise NotImplementedError
