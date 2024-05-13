from dataclasses import dataclass
from typing import ClassVar

from opendevin.events.event import Event


@dataclass
class Action(Event):
    runnable: ClassVar[bool] = False

    def to_memory(self):
        d = super().to_memory()
        try:
            v = d.pop('action')
        except KeyError:
            raise NotImplementedError(f'{self=} does not have action attribute set')
        return {'action': v, 'args': d}
