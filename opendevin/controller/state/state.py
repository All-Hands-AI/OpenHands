from dataclasses import dataclass, field

from opendevin.controller.state.plan import Plan
from opendevin.events.action import (
    Action,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    Observation,
)


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
    error: str | None = None
