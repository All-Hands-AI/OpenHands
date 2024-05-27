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
    last_browser_action_error: str = ''
    focused_element_bid: str = ''

    @property
    def message(self) -> str:
        return 'Visited ' + self.url

    def __str__(self) -> str:
        return (
            '**BrowserOutputObservation**\n'
            f'URL: {self.url}\n'
            f'Status code: {self.status_code}\n'
            f'Error: {self.error}\n'
            f'Open pages: {self.open_pages_urls}\n'
            f'Active page index: {self.active_page_index}\n'
            f'Last browser action: {self.last_browser_action}\n'
            f'Last browser action error: {self.last_browser_action_error}\n'
            f'Focused element bid: {self.focused_element_bid}\n'
            f'CONTENT: {self.content}\n'
        )
