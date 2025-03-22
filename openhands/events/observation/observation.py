from dataclasses import dataclass, field

from openhands.events.event import Event


@dataclass
class Observation(Event):
    content: str
    response_id: str = field(default="")
