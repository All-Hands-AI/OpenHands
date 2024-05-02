import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.core.schema import ActionType
from opendevin.events.observation import BrowserOutputObservation

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class BrowseURLAction(Action):
    url: str
    thought: str = ''
    action: str = ActionType.BROWSE

    async def run(self, controller: 'AgentController') -> BrowserOutputObservation:  # type: ignore
        asked_url = self.url
        if not asked_url.startswith('http'):
            asked_url = os.path.abspath(os.curdir) + self.url
        try:
            # action in BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/functions.py
            action_str = f'goto("{asked_url}")'
            # obs provided by BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/env.py#L396
            obs = controller.browser.step(action_str)
            return BrowserOutputObservation(
                content=obs['text_content'],  # text content of the page
                open_pages_urls=obs['open_pages_urls'],  # list of open pages
                active_page_index=obs['active_page_index'],  # index of the active page
                dom_object=obs['dom_object'],  # DOM object
                axtree_object=obs['axtree_object'],  # accessibility tree object
                last_browser_action=obs[
                    'last_action'
                ],  # last browser env action performed
                focused_element_bid=obs['focused_element_bid'],  # focused element bid
                screenshot=obs['screenshot'],  # base64-encoded screenshot, png
                url=asked_url,
            )
        except Exception as e:
            return BrowserOutputObservation(
                content=str(e), screenshot='', error=True, url=asked_url
            )

    @property
    def message(self) -> str:
        return f'Browsing URL: {self.url}'
