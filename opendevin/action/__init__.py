from .base import Action, NullAction
from .bash import CmdRunAction, CmdKillAction
from .browse import BrowseURLAction
from .fileop import FileReadAction, FileWriteAction
from .agent import AgentRecallAction, AgentThinkAction, AgentFinishAction, AgentEchoAction

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
]

ACTION_TYPE_TO_CLASS = {
    "run": CmdRunAction,
    "kill": CmdKillAction,
    "browse": BrowseURLAction,
    "read": FileReadAction,
    "write": FileWriteAction,
    "recall": AgentRecallAction,
    "think": AgentThinkAction,
    "finish": AgentFinishAction,
}
