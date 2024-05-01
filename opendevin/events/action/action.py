from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.events.event import Event

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.events.observation import Observation


@dataclass
class Action(Event):
    async def run(self, controller: 'AgentController') -> 'Observation':
        raise NotImplementedError

    def to_memory(self):
        d = super().to_memory()
        try:
            v = d.pop('action')
        except KeyError:
            raise NotImplementedError(f'{self=} does not have action attribute set')
        return {'action': v, 'args': d}

    @property
    def executable(self) -> bool:
        raise NotImplementedError
