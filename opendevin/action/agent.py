from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.observation import AgentRecallObservation, AgentMessageObservation, Observation
from .base import ExecutableAction, NotExecutableAction
if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AgentRecallAction(ExecutableAction):
    query: str

    def run(self, controller: "AgentController") -> AgentRecallObservation:
        return AgentRecallObservation(
            content="Recalling memories...",
            memories=controller.agent.search_memory(self.query)
        )

    @property
    def message(self) -> str:
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."



@dataclass
class AgentThinkAction(NotExecutableAction):
    thought: str
    runnable: bool = False

    def run(self, controller: "AgentController") -> "Observation":
        raise NotImplementedError

    @property
    def message(self) -> str:
        return self.thought


@dataclass
class AgentEchoAction(ExecutableAction):
    content: str
    runnable: bool = True

    def run(self, controller: "AgentController") -> "Observation":
        return AgentMessageObservation(self.content)

    @property
    def message(self) -> str:
        return self.content

@dataclass
class AgentSummarizeAction(NotExecutableAction):
    summary: str

    @property
    def message(self) -> str:
        return self.summary

@dataclass
class AgentFinishAction(NotExecutableAction):
    runnable: bool = False

    def run(self, controller: "AgentController") -> "Observation":
        raise NotImplementedError

    @property
    def message(self) -> str:
        return "All done! What's next on the agenda?"

