from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.observation import AgentRecallObservation, AgentMessageObservation, Observation
from .base import ExecutableAction, NotExecutableAction

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class AgentRecallAction(ExecutableAction):
    query: str
    action: str = "recall"

    def run(self, controller: "AgentController") -> AgentRecallObservation:
        """
        Runs the action to recall memories based on the provided query.

        Args:
            controller (AgentController): The agent controller.

        Returns:
            AgentRecallObservation: Observation containing recalled memories.
        """
        try:
            memories = controller.agent.search_memory(self.query)
            return AgentRecallObservation(
                content="Recalling memories...",
                memories=memories
            )
        except Exception as e:
            # Log the error or handle it appropriately based on your application's requirements
            raise RuntimeError(f"Error while recalling memories: {e}")

    @property
    def message(self) -> str:
        """
        Returns a message indicating the action being performed.

        Returns:
            str: Message indicating the action.
        """
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."


@dataclass
class AgentThinkAction(NotExecutableAction):
    thought: str
    action: str = "think"

    def run(self, controller: "AgentController") -> Observation:
        """
        Raises NotImplementedError as this action is not executable.

        Args:
            controller (AgentController): The agent controller.

        Raises:
            NotImplementedError: Always raised as this action is not executable.
        """
        raise NotImplementedError("AgentThinkAction is not executable")

    @property
    def message(self) -> str:
        """
        Returns the thought associated with this action.

        Returns:
            str: The thought associated with this action.
        """
        return self.thought


@dataclass
class AgentEchoAction(ExecutableAction):
    content: str
    action: str = "echo"

    def run(self, controller: "AgentController") -> Observation:
        """
        Runs the action to echo the provided content.

        Args:
            controller (AgentController): The agent controller.

        Returns:
            AgentMessageObservation: Observation containing echoed message.
        """
        return AgentMessageObservation(self.content)

    @property
    def message(self) -> str:
        """
        Returns the content associated with this action.

        Returns:
            str: The content associated with this action.
        """
        return self.content


@dataclass
class AgentSummarizeAction(NotExecutableAction):
    summary: str
    action: str = "summarize"

    @property
    def message(self) -> str:
        """
        Returns the summary associated with this action.

        Returns:
            str: The summary associated with this action.
        """
        return self.summary


@dataclass
class AgentFinishAction(NotExecutableAction):
    action: str = "finish"

    def run(self, controller: "AgentController") -> Observation:
        """
        Raises NotImplementedError as this action is not executable.

        Args:
            controller (AgentController): The agent controller.

        Raises:
            NotImplementedError: Always raised as this action is not executable.
        """
        raise NotImplementedError("AgentFinishAction is not executable")

    @property
    def message(self) -> str:
        """
        Returns a completion message.

        Returns:
            str: A completion message.
        """
        return "All done! What's next on the agenda?"
