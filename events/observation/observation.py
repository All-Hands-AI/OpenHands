from dataclasses import dataclass

from openhands.events.event import Event


@dataclass
class Observation(Event):
    content: str
