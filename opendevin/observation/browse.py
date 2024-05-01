from dataclasses import dataclass, field

from opendevin.schema import ObservationType

from .base import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    screenshot: str = ''
    status_code: int = 200
    error: bool = False
    observation: str = ObservationType.BROWSE
    # do not include in the memory
    open_pages_urls: list = field(default_factory=list)
    active_page_index: int = -1
    dom_object: dict = field(default_factory=dict)
    axtree_object: dict = field(default_factory=dict)
    last_action: str = ''
    focused_element_bid: str = ''

    def to_memory(self) -> dict:
        memory_dict = super().to_memory()
        # remove some fields from the memory, as currently they are too big for LLMs
        # TODO: find a more elegant way to handle this
        memory_dict['extras'].pop('dom_object', None)
        memory_dict['extras'].pop('axtree_object', None)
        memory_dict['extras'].pop('open_pages_urls', None)
        memory_dict['extras'].pop('active_page_index', None)
        memory_dict['extras'].pop('last_action', None)
        memory_dict['extras'].pop('focused_element_bid', None)
        return memory_dict

    @property
    def message(self) -> str:
        return 'Visited ' + self.url
