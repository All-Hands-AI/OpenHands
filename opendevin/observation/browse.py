from dataclasses import dataclass

from .base import Observation

@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    status_code: int = 200
    error: bool = False
    observation : str = "browse"

    @property
    def message(self) -> str:
        return "Visited " + self.url



