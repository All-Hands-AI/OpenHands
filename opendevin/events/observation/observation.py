from dataclasses import dataclass

from opendevin.events.event import Event


@dataclass
class Observation(Event):
    content: str
