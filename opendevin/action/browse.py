import os
import uuid
import html2text

from multiprocessing.connection import Connection
from dataclasses import dataclass
from opendevin.observation import BrowserOutputObservation
from opendevin.schema import ActionType
from typing import TYPE_CHECKING
from browsergym.utils.obs import flatten_dom_to_str

from .base import ExecutableAction

if TYPE_CHECKING:
    from opendevin.controller import AgentController


def browser_env_step(action_str: str, conn: Connection):
    unique_request_id = str(uuid.uuid4())
    conn.send((unique_request_id, {'action': action_str}))
    while True:
        if conn.poll():
            response_id, response = conn.recv()
            if response_id == unique_request_id:
                return response


@dataclass
class BrowseURLAction(ExecutableAction):
    url: str
    action: str = ActionType.BROWSE

    async def run(self, controller: 'AgentController') -> BrowserOutputObservation:  # type: ignore
        asked_url = self.url
        if not asked_url.startswith('http'):
            asked_url = os.path.abspath(os.curdir) + self.url
        try:
            action_str = f'goto("{asked_url}")'
            obs = browser_env_step(action_str, controller.agent_side)
            if obs['last_action_error']:
                return BrowserOutputObservation(
                    content=obs['last_action_error'], screenshot='', error=True, url=asked_url
                )

            text_content = html2text.html2text(flatten_dom_to_str(obs['dom_object']))
            return BrowserOutputObservation(
                content=text_content,  # text content of the page
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
