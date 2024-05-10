from dataclasses import dataclass, field

from opendevin.core.schema import ObservationType

from .observation import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    screenshot: str = field(repr=False)  # don't show in repr
    status_code: int = 200
    error: bool = False
    observation: str = ObservationType.BROWSE
    # do not include in the memory
    open_pages_urls: list = field(default_factory=list)
    active_page_index: int = -1
    dom_object: dict = field(default_factory=dict, repr=False)  # don't show in repr
    axtree_object: dict = field(default_factory=dict, repr=False)  # don't show in repr
    last_browser_action: str = ''
    focused_element_bid: str = ''

    @property
    def message(self) -> str:
        return 'Visited ' + self.url
