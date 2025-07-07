from __future__ import annotations

from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.llm.metrics_registry import MetricsRegistry
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, view: View) -> View | Condensation:
        """Returns the list of events unchanged."""
        return view

    @classmethod
    def from_config(
        cls, config: NoOpCondenserConfig, metrics_registry: MetricsRegistry
    ) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
