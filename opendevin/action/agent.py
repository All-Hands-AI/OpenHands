from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.observation import AgentMessageObservation, Observation
from .base import NotExecutableAction
if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AgentRecallAction(ExecutableAction):
    query: str

    def run(self, controller: "AgentController") -> AgentMessageObservation:
        return AgentMessageObservation(controller.agent.search_memory(self.query))


@dataclass
class AgentThinkAction(NotExecutableAction):
    thought: str
    runnable: bool = False

    def run(self, controller: "AgentController") -> "Observation":
        raise NotImplementedError


@dataclass
class AgentFinishAction(NotExecutableAction):
    runnable: bool = False

    def run(self, controller: "AgentController") -> "Observation":
        raise NotImplementedError
