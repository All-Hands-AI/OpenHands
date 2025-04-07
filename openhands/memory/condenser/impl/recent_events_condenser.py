from __future__ import annotations

from openhands.core.config.condenser_config import RecentEventsCondenserConfig
from openhands.events.event import Event
from openhands.memory.condenser.condenser import Condenser


class RecentEventsCondenser(Condenser):
    """A condenser that only keeps a certain number of the most recent events."""

    def __init__(self, keep_first: int = 0, max_events: int = 10):
        self.keep_first = keep_first
        self.max_events = max_events

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Keep only the most recent events (up to `max_events`)."""
        head = events[: self.keep_first]
        tail_length = max(0, self.max_events - len(head))
        tail = events[-tail_length:]
        return head + tail

    @classmethod
    def from_config(cls, config: RecentEventsCondenserConfig) -> RecentEventsCondenser:
        return RecentEventsCondenser(**config.model_dump(exclude=['type']))


RecentEventsCondenser.register_config(RecentEventsCondenserConfig)
