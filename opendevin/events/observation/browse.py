from dataclasses import dataclass, field

from opendevin.core.schema import ObservationType

from .observation import Observation


def _remove_fields(obj, fields: set[str]):
    """
    Remove fields from an object

    Parameters:
    - obj (Object): The object to remove fields from
    - fields (set[str]): A set of field names to remove from the object
    """
    if isinstance(obj, dict):
        for field in fields:
            if field in obj:
                del obj[field]
        for _, value in obj.items():
            _remove_fields(value, fields)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for item in obj:
            _remove_fields(item, fields)
    elif hasattr(obj, '__dataclass_fields__'):
        for field in fields:
            if field in obj.__dataclass_fields__:
                setattr(obj, field, None)
        for value in obj.__dict__.values():
            _remove_fields(value, fields)


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

    def to_memory(self) -> dict:
        memory_dict = super().to_memory()
        # remove some fields from the memory, as currently they are too big for LLMs
        _remove_fields(
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
