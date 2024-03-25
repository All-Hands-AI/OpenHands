from dataclasses import dataclass
from typing import List, Tuple

from opendevin.action import (
    Action,
)
from opendevin.observation import (
    Observation,
    CmdOutputObservation,
)


@dataclass
class State:
    background_commands_obs: List[CmdOutputObservation]
    updated_info: List[Tuple[Action, Observation]]
