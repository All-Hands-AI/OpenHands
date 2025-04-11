from __future__ import annotations

from typing import Any, cast

from openhands.core.config.condenser_config import RecentEventsCondenserConfig
from openhands.events.action.message import SystemMessageAction
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class RecentEventsCondenser(Condenser):
    """A condenser that only keeps a certain number of the most recent events."""

    def __init__(self, keep_first: int = 1, max_events: int = 10):
        self.keep_first = keep_first
        self.max_events = max_events

        super().__init__()

    def condense(self, view: View) -> View | Condensation:
        """Keep only the most recent events (up to `max_events`), always including SystemMessageAction."""
        # Find any SystemMessageAction in the view
        system_messages = [
            event for event in view if isinstance(event, SystemMessageAction)
        ]

        # Keep the first events as specified
        head = view[: self.keep_first]

        # Calculate how many events we can include in the tail
        # Accounting for system messages that we'll always include
        tail_length = max(0, self.max_events - len(head) - len(system_messages))
        tail = view[-tail_length:]

        # Combine system messages, head, and tail
        # Ensure we don't duplicate system messages that might be in head or tail
        result_events = []

        # Add system messages first
        for event in system_messages:
            if event not in head and event not in tail:
                result_events.append(event)

        # Add head and tail - cast to Any to satisfy type checker
        result_events.extend(cast(list[Any], head))
        result_events.extend(cast(list[Any], tail))

        return View(events=result_events)

    @classmethod
    def from_config(cls, config: RecentEventsCondenserConfig) -> RecentEventsCondenser:
        return RecentEventsCondenser(**config.model_dump(exclude=['type']))


RecentEventsCondenser.register_config(RecentEventsCondenserConfig)
