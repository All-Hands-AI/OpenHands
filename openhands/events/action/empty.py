from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action
from openhands.events.observation.observation import Observation


@dataclass
class NullAction(Action):
    """An action that does nothing."""

    action: str = ActionType.NULL
    # NullAction will add `next_obs` to the event stream if it is not None
    next_obs: Observation | None = None

    @property
    def message(self) -> str:
        return 'No action'
