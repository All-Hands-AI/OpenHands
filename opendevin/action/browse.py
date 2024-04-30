import base64
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright

from opendevin.observation import BrowserOutputObservation
from opendevin.schema import ActionType

from .base import ExecutableAction

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class BrowseURLAction(ExecutableAction):
    url: str
    action: str = ActionType.BROWSE

    async def run(self, controller: 'AgentController') -> BrowserOutputObservation:  # type: ignore
        asked_url = self.url
        if not asked_url.startswith('http'):
            asked_url = os.path.abspath(os.curdir) + self.url
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                response = await page.goto(asked_url)
                try:
                    # domcontentloaded: Wait for the DOMContentLoaded event to be fired.
                    # load: Wait for the load event to be fired.
                    # networkidle: Wait until there are no more network connections
                    await page.wait_for_load_state('networkidle', timeout=3000)
                except TimeoutError:
                    pass
                # content = await page.content()
                inner_text = await page.evaluate('() => document.body.innerText')
                screenshot_bytes = await page.screenshot(full_page=True)
                await browser.close()

                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return BrowserOutputObservation(
                    content=inner_text,  # HTML content of the page
                    screenshot=screenshot_base64,  # Base64-encoded screenshot
                    url=asked_url,
                    status_code=response.status if response else 0,  # HTTP status code
                )
        except Exception as e:
            return BrowserOutputObservation(
                content=str(e), screenshot='', error=True, url=asked_url
            )

    @property
    def message(self) -> str:
        return f'Browsing URL: {self.url}'
