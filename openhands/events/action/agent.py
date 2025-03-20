from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openhands.core.schema import ActionType
from openhands.events.action.action import Action
from openhands.events.event import RecallType


@dataclass
class ChangeAgentStateAction(Action):
    """Fake action, just to notify the client that a task state has changed."""

    agent_state: str
    thought: str = ''
    action: str = ActionType.CHANGE_AGENT_STATE

    @property
    def message(self) -> str:
        return f'Agent state changed to {self.agent_state}'


@dataclass
class AgentSummarizeAction(Action):
    summary: str
    action: str = ActionType.SUMMARIZE

    @property
    def message(self) -> str:
        return self.summary

    def __str__(self) -> str:
        ret = '**AgentSummarizeAction**\n'
        ret += f'SUMMARY: {self.summary}'
        return ret


class AgentFinishTaskCompleted(Enum):
    FALSE = 'false'
    PARTIAL = 'partial'
    TRUE = 'true'


@dataclass
class AgentFinishAction(Action):
    """An action where the agent finishes the task.

    Attributes:
        final_thought (str): The message to send to the user.
        task_completed (enum): Whether the agent believes the task has been completed.
        outputs (dict): The other outputs of the agent, for instance "content".
        thought (str): The agent's explanation of its actions.
        action (str): The action type, namely ActionType.FINISH.
    """

    final_thought: str = ''
    task_completed: AgentFinishTaskCompleted | None = None
    outputs: dict[str, Any] = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.FINISH

    @property
    def message(self) -> str:
        if self.thought != '':
            return self.thought
        return "All done! What's next on the agenda?"


@dataclass
class AgentThinkAction(Action):
    """An action where the agent logs a thought.

    Attributes:
        thought (str): The agent's explanation of its actions.
        action (str): The action type, namely ActionType.THINK.
    """

    thought: str = ''
    action: str = ActionType.THINK

    @property
    def message(self) -> str:
        return f'I am thinking...: {self.thought}'


@dataclass
class AgentRejectAction(Action):
    outputs: dict = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.REJECT

    @property
    def message(self) -> str:
        msg: str = 'Task is rejected by the agent.'
        if 'reason' in self.outputs:
            msg += ' Reason: ' + self.outputs['reason']
        return msg


@dataclass
class AgentDelegateAction(Action):
    agent: str
    inputs: dict
    thought: str = ''
    action: str = ActionType.DELEGATE

    @property
    def message(self) -> str:
        return f"I'm asking {self.agent} for help with this task."


@dataclass
class RecallAction(Action):
    """This action is used for retrieving content, e.g., from the global directory or user workspace."""

    recall_type: RecallType
    query: str = ''
    thought: str = ''
    action: str = ActionType.RECALL

    @property
    def message(self) -> str:
        return f'Retrieving content for: {self.query[:50]}'

    def __str__(self) -> str:
        ret = '**RecallAction**\n'
        ret += f'QUERY: {self.query[:50]}'
        return ret
