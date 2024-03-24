from dataclasses import dataclass
from typing import Mapping, List

from opendevin.action import (
    Action,
)
from opendevin.observation import (
    Observation,
    CmdOutputObservation,
)


@dataclass
class State:
    background_commands_obs: Mapping[int, CmdOutputObservation]
    updated_info: List[Action | Observation]
