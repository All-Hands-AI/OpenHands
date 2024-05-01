from dataclasses import dataclass

from opendevin.schema import ObservationType

from .base import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    screenshot: str = ''
    open_pages_urls: list = []
    active_page_index: int = -1
    dom_object: dict = {}
    axtree_object: dict = {}
    last_action: str = ''
    focused_element_bid: str = ''
    status_code: int = 200
    error: bool = False
    observation: str = ObservationType.BROWSE

    @property
    def message(self) -> str:
        return 'Visited ' + self.url
