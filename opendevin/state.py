from dataclasses import dataclass
from typing import Mapping, List

from opendevin.action import (
    Action,
    CmdRunAction,
    CmdKillAction,
    BrowseURLAction,
    FileReadAction,
    FileWriteAction,
    AgentRecallAction,
    AgentThinkAction,
    AgentFinishAction,
)
from opendevin.observation import (
    Observation,
    CmdOutputObservation,
    UserMessageObservation,
    AgentMessageObservation,
    BrowserOutputObservation,
)


@dataclass
class State:
    background_commands_obs: Mapping[int, CmdOutputObservation]
    updated_info: List[Action | Observation]
