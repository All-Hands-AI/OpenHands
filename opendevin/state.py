from dataclasses import dataclass, field

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
    iteration: int = 0
    background_commands_obs: list[CmdOutputObservation] = field(
        default_factory=list)
    history: list[tuple[Action, Observation]] = field(default_factory=list)
    updated_info: list[tuple[Action, Observation]
                       ] = field(default_factory=list)
