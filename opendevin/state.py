from dataclasses import dataclass, field

from opendevin.action import (
    Action,
)
from opendevin.observation import (
    CmdOutputObservation,
    Observation,
)
from opendevin.plan import Plan


@dataclass
class State:
    plan: Plan
    iteration: int = 0
    # number of characters we have sent to and received from LLM so far for current task
    num_of_chars: int = 0
    background_commands_obs: list[CmdOutputObservation] = field(default_factory=list)
    history: list[tuple[Action, Observation]] = field(default_factory=list)
    updated_info: list[tuple[Action, Observation]] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
