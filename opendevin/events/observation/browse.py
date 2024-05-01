from dataclasses import dataclass

from opendevin.schema import ObservationType

from .observation import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    screenshot: str
    status_code: int = 200
    error: bool = False
    observation: str = ObservationType.BROWSE

    @property
    def message(self) -> str:
        return 'Visited ' + self.url
