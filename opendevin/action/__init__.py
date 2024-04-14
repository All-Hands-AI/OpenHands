from .base import Action, NullAction
from .bash import CmdRunAction, CmdKillAction
from .browse import BrowseURLAction
from .fileop import FileReadAction, FileWriteAction
from .agent import (
    AgentRecallAction,
    AgentThinkAction,
    AgentFinishAction,
    AgentEchoAction,
    AgentSummarizeAction,
)
from .tasks import AddTaskAction, ModifyTaskAction

actions = (
    CmdKillAction,
    CmdRunAction,
    BrowseURLAction,
    FileReadAction,
    FileWriteAction,
    AgentRecallAction,
    AgentThinkAction,
    AgentFinishAction,
    AddTaskAction,
    ModifyTaskAction,
)

ACTION_TYPE_TO_CLASS = {action_class.action: action_class for action_class in actions}  # type: ignore[attr-defined]


def action_from_dict(action: dict) -> Action:
    action = action.copy()
    if "action" not in action:
        raise KeyError(f"'action' key is not found in {action=}")
    action_class = ACTION_TYPE_TO_CLASS.get(action["action"])
    if action_class is None:
        raise KeyError(
            f"'{action['action']=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}"
        )
    args = action.get("args", {})
    return action_class(**args)


__all__ = [
    "Action",
    "NullAction",
    "CmdRunAction",
    "CmdKillAction",
    "BrowseURLAction",
    "FileReadAction",
    "FileWriteAction",
    "AgentRecallAction",
    "AgentThinkAction",
    "AgentFinishAction",
    "AgentEchoAction",
    "AgentSummarizeAction",
    "AddTaskAction",
    "ModifyTaskAction",
]
