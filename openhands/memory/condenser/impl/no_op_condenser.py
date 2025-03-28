from __future__ import annotations

from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

<<<<<<< HEAD
    def condense(self, view: View) -> View | Condensation:
        """Returns the list of events unchanged."""
        return view
=======
    def condense(self, events: list[Event]) -> View | Condensation:
        """Returns the list of events unchanged."""
        return View(events=events)
>>>>>>> 9f2a39382 (Revert "add force argument")

    @classmethod
    def from_config(cls, config: NoOpCondenserConfig) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
