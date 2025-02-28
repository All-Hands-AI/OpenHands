from __future__ import annotations

from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.events.event import Event
from openhands.memory.condenser.condenser import Condenser


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event]) -> list[Event]:
        """Returns the list of events unchanged."""
        return events

    @classmethod
    def from_config(cls, config: NoOpCondenserConfig) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
