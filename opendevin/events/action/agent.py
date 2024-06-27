from dataclasses import dataclass, field
from typing import ClassVar

from opendevin.core.schema import ActionType

from .action import Action


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
class AgentRecallAction(Action):
    query: str
    thought: str = ''
    action: str = ActionType.RECALL
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f"Let me dive into my memories to find what you're looking for! Searching for: '{self.query}'. This might take a moment."


@dataclass
class AgentSummarizeAction(Action):
    """
    Action to summarize a list of events.

    Attributes:
    - summarized_actions: A sentence summarizing all the actions.
    - summarized_observations: A few sentences summarizing all the observations.
    """

    summarized_actions: str = ''
    summarized_observations: str = ''
    action: str = ActionType.SUMMARIZE
    _chunk_start: int = -1
    _chunk_end: int = -1
    is_delegate_summary: bool = False

    @property
    def message(self) -> str:
        return self.summarized_observations

    def __str__(self) -> str:
        ret = '**AgentSummarizeAction**\n'
        ret += f'SUMMARIZED ACTIONS: {self.summarized_actions}\n'
        ret += f'SUMMARIZED OBSERVATIONS: {self.summarized_observations}\n'
        return ret


@dataclass
class AgentFinishAction(Action):
    outputs: dict = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.FINISH

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
