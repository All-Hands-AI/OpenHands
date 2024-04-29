from .base import Action, NullAction
from .bash import CmdRunAction, CmdKillAction, IPythonRunCellAction
from .browse import BrowseURLAction
from .fileop import FileReadAction, FileWriteAction
from .github import GitHubPushAction
from .agent import (
    AgentRecallAction,
    AgentThinkAction,
    AgentTalkAction,
    AgentFinishAction,
    AgentEchoAction,
    AgentSummarizeAction,
    AgentDelegateAction,
)
from .tasks import AddTaskAction, ModifyTaskAction
from ..exceptions import AgentMalformedActionError

actions = (
    CmdKillAction,
    CmdRunAction,
    IPythonRunCellAction,
    BrowseURLAction,
    FileReadAction,
    FileWriteAction,
    AgentRecallAction,
    AgentThinkAction,
    AgentTalkAction,
    AgentFinishAction,
    AgentDelegateAction,
    AddTaskAction,
    ModifyTaskAction,
    GitHubPushAction,
)

ACTION_TYPE_TO_CLASS = {action_class.action: action_class for action_class in actions}  # type: ignore[attr-defined]


def action_from_dict(action: dict) -> Action:
    if not isinstance(action, dict):
        raise AgentMalformedActionError('action must be a dictionary')
    action = action.copy()
    if 'action' not in action:
        raise AgentMalformedActionError(f"'action' key is not found in {action=}")
    action_class = ACTION_TYPE_TO_CLASS.get(action['action'])
    if action_class is None:
        raise AgentMalformedActionError(
            f"'{action['action']=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}"
        )
    args = action.get('args', {})
    try:
        decoded_action = action_class(**args)
    except TypeError:
        raise AgentMalformedActionError(f'action={action} has the wrong arguments')
    return decoded_action


__all__ = [
    'Action',
    'NullAction',
    'CmdRunAction',
    'CmdKillAction',
    'BrowseURLAction',
    'FileReadAction',
    'FileWriteAction',
    'AgentRecallAction',
    'AgentThinkAction',
    'AgentTalkAction',
    'AgentFinishAction',
    'AgentDelegateAction',
    'AgentEchoAction',
    'AgentSummarizeAction',
    'AddTaskAction',
    'ModifyTaskAction',
    'IPythonRunCellAction'
]
