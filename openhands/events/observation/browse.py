from dataclasses import dataclass, field
from typing import Any

from browsergym.utils.obs import flatten_axtree_to_str

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """This data class represents the output of a browser."""

    url: str
    trigger_by_action: str
    screenshot: str = field(repr=False, default='')  # don't show in repr
    screenshot_path: str | None = field(default=None)  # path to saved screenshot file
    set_of_marks: str = field(default='', repr=False)  # don't show in repr
    error: bool = False
    observation: str = ObservationType.BROWSE
    goal_image_urls: list[str] = field(default_factory=list)
    # do not include in the memory
    open_pages_urls: list[str] = field(default_factory=list)
    active_page_index: int = -1
    dom_object: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    axtree_object: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    extra_element_properties: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    last_browser_action: str = ''
    last_browser_action_error: str = ''
    focused_element_bid: str = ''

    @property
    def message(self) -> str:
        return 'Visited ' + self.url

    def __str__(self) -> str:
        ret = (
            '**BrowserOutputObservation**\n'
            f'URL: {self.url}\n'
            f'Error: {self.error}\n'
            f'Open pages: {self.open_pages_urls}\n'
            f'Active page index: {self.active_page_index}\n'
            f'Last browser action: {self.last_browser_action}\n'
            f'Last browser action error: {self.last_browser_action_error}\n'
            f'Focused element bid: {self.focused_element_bid}\n'
        )
        if self.screenshot_path:
            ret += f'Screenshot saved to: {self.screenshot_path}\n'
        ret += '--- Agent Observation ---\n'
        ret += self.content
        return ret

    # The get_agent_obs_text method has been moved to openhands/runtime/browser/utils.py

    def get_axtree_str(self, filter_visible_only: bool = False) -> str:
        cur_axtree_txt = flatten_axtree_to_str(
            self.axtree_object,
            extra_properties=self.extra_element_properties,
            with_clickable=True,
            skip_generic=False,
            filter_visible_only=filter_visible_only,
        )
        return str(cur_axtree_txt)
