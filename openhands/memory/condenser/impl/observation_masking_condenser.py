from __future__ import annotations

from openhands.core.config.condenser_config import ObservationMaskingCondenserConfig
from openhands.events.event import Event
from openhands.events.observation import Observation
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.memory.condenser.condenser import Condenser


class ObservationMaskingCondenser(Condenser):
    """A condenser that masks the values of observations outside of a recent attention window."""

    def __init__(self, attention_window: int = 5):
        self.attention_window = attention_window

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Replace the content of observations outside of the attention window with a placeholder."""
        results: list[Event] = []
        for i, event in enumerate(events):
            if (
                isinstance(event, Observation)
                and i < len(events) - self.attention_window
            ):
                results.append(AgentCondensationObservation('<MASKED>'))
            else:
                results.append(event)

        return results

    @classmethod
    def from_config(
        cls, config: ObservationMaskingCondenserConfig
    ) -> ObservationMaskingCondenser:
        return ObservationMaskingCondenser(**config.model_dump(exclude=['type']))


ObservationMaskingCondenser.register_config(ObservationMaskingCondenserConfig)
