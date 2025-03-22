from __future__ import annotations

from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.events.event import Event
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event]) -> View | Condensation:
        """Returns the list of events unchanged."""
        return View(events=events)

    @classmethod
    def from_config(cls, config: NoOpCondenserConfig) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
