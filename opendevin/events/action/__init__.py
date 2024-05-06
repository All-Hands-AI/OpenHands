from opendevin.core.exceptions import AgentMalformedActionError

from .action import Action
from .agent import (
    AgentDelegateAction,
    AgentEchoAction,
    AgentFinishAction,
    AgentRecallAction,
    AgentSummarizeAction,
    AgentTalkAction,
    AgentThinkAction,
    ChangeAgentStateAction,
)
from .browse import BrowseURLAction
from .commands import CmdKillAction, CmdRunAction, IPythonRunCellAction
from .empty import NullAction
from .files import FileReadAction, FileWriteAction
from .github import GitHubPushAction
from .message import MessageAction
from .tasks import AddTaskAction, ModifyTaskAction

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
    ChangeAgentStateAction,
    GitHubPushAction,
    MessageAction,
)

ACTION_TYPE_TO_CLASS = {action_class.action: action_class for action_class in actions}  # type: ignore[attr-defined]


def action_from_dict(action: dict) -> Action:
    if not isinstance(action, dict):
        raise AgentMalformedActionError('action must be a dictionary')
    action = action.copy()
    if 'action' not in action:
        raise AgentMalformedActionError(f"'action' key is not found in {action=}")
    if not isinstance(action['action'], str):
        raise AgentMalformedActionError(
            f"'{action['action']=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}"
        )
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
    'ChangeAgentStateAction',
    'IPythonRunCellAction',
    'MessageAction',
]
