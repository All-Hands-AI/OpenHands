from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.events.event import Event

if TYPE_CHECKING:
    pass


@dataclass
class Action(Event):
    @property
    def runnable(self):
        return False

    def to_memory(self):
        d = super().to_memory()
        try:
            v = d.pop('action')
        except KeyError:
            raise NotImplementedError(f'{self=} does not have action attribute set')
        return {'action': v, 'args': d}
