from dataclasses import dataclass, field

from opendevin.core.schema import ObservationType
from opendevin.events.utils import remove_fields

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

    def to_dict(self):
        dictionary = super().to_dict()
        # add screenshot for frontend showcase only, not for agent consumption
        dictionary['screenshot'] = self.screenshot
        return dictionary

    def to_memory(self) -> dict:
        memory_dict = super().to_memory()
        # remove some fields from the memory, as currently they are too big for LLMs
        remove_fields(
            memory_dict['extras'],
            {
                'screenshot',
                'dom_object',
                'axtree_object',
                'open_pages_urls',
                'active_page_index',
                'last_browser_action',
                'focused_element_bid',
            },
        )
        return memory_dict

    @property
    def message(self) -> str:
        return 'Visited ' + self.url
