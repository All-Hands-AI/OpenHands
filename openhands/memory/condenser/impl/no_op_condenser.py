from __future__ import annotations

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, view: View, state: State, agent=None) -> View | Condensation:
        """Returns the list of events unchanged."""
        return view

    @classmethod
    def from_config(cls, config: NoOpCondenserConfig) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
