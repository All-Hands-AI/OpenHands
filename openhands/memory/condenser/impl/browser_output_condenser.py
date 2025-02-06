from __future__ import annotations

from openhands.core.config.condenser_config import BrowserOutputCondenserConfig
from openhands.events.event import Event
from openhands.events.observation import BrowserOutputObservation
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.memory.condenser.condenser import Condenser


class BrowserOutputCondenser(Condenser):
    """A condenser that masks the observations from browser outputs outside of a recent attention window."""

    def __init__(self, attention_window: int = 1):
        self.attention_window = attention_window
        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Replace the content of browser observations outside of the attention window with a placeholder."""
        results: list[Event] = []
        cnt: int = 0
        for event in reversed(events):
            if (
                isinstance(event, BrowserOutputObservation)
                and cnt >= self.attention_window
            ):
                results.append(AgentCondensationObservation('<MASKED>'))
            else:
                results.append(event)
                if isinstance(event, BrowserOutputObservation):
                    cnt += 1

        return list(reversed(results))

    @classmethod
    def from_config(
        cls, config: BrowserOutputCondenserConfig
    ) -> BrowserOutputCondenser:
        return BrowserOutputCondenser(**config.model_dump(exclude=['type']))


BrowserOutputCondenser.register_config(BrowserOutputCondenserConfig)
