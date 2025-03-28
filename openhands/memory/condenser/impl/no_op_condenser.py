from __future__ import annotations

from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.events.event import Event
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event], force: bool = False) -> View | Condensation:
        """Returns the list of events unchanged.

        Args:
            events: A list of events representing the entire history of the agent.
            force: If True, force condensation regardless of normal conditions.
                  Not used by this condenser as it never condenses events.

        Returns:
            View: A view containing all the original events.
        """
        return View(events=events)

    @classmethod
    def from_config(cls, config: NoOpCondenserConfig) -> NoOpCondenser:
        return NoOpCondenser()


NoOpCondenser.register_config(NoOpCondenserConfig)
