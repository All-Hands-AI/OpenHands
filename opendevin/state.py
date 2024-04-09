from dataclasses import dataclass, field
from typing import List, Tuple

from opendevin.plan import Plan

from opendevin.action import (
    Action,
)
from opendevin.observation import (
    Observation,
    CmdOutputObservation,
)


@dataclass
class State:
    plan: Plan
    working_dir: str
    iteration: int = 0
    file_name: str = ''
    cur_line: int = 0
    background_commands_obs: List[CmdOutputObservation] = field(
        default_factory=list)
    history: List[Tuple[Action, Observation]] = field(default_factory=list)
    updated_info: List[Tuple[Action, Observation]
                       ] = field(default_factory=list)
