from typing import ClassVar

from pydantic import Field

from opendevin.core.schema import ObservationType
from opendevin.events.utils import remove_fields

from .observation import Observation


class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    screenshot: str = Field(repr=False)  # don't show in repr
    status_code: int = 200
    error: bool = False
    observation: ClassVar[str] = ObservationType.BROWSE
    # do not include in the memory
    open_pages_urls: list = Field(default_factory=list)
    active_page_index: int = -1
    dom_object: dict = Field(default_factory=dict, repr=False)  # don't show in repr
    axtree_object: dict = Field(default_factory=dict, repr=False)  # don't show in repr
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
