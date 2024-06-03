import os

from opendevin.core.exceptions import BrowserUnavailableException
from opendevin.core.schema import ActionType
from opendevin.events.observation import BrowserOutputObservation
from opendevin.runtime.browser.browser_env import BrowserEnv


async def browse(action, browser: BrowserEnv | None) -> BrowserOutputObservation:
    if browser is None:
        raise BrowserUnavailableException()
    if action.action == ActionType.BROWSE:
        # legacy BrowseURLAction
        asked_url = action.url
        if not asked_url.startswith('http'):
            asked_url = os.path.abspath(os.curdir) + action.url
        action_str = f'goto("{asked_url}")'
    elif action.action == ActionType.BROWSE_INTERACTIVE:
        # new BrowseInteractiveAction, supports full featured BrowserGym actions
        # action in BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/functions.py
        action_str = action.browser_actions
    else:
        raise ValueError(f'Invalid action type: {action.action}')
    try:
        # obs provided by BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/env.py#L396
        obs = browser.step(action_str)
        return BrowserOutputObservation(
            content=obs['text_content'],  # text content of the page
            open_pages_urls=obs['open_pages_urls'],  # list of open pages
            active_page_index=obs['active_page_index'],  # index of the active page
            dom_object=obs['dom_object'],  # DOM object
            axtree_object=obs['axtree_object'],  # accessibility tree object
            last_browser_action=obs['last_action'],  # last browser env action performed
            focused_element_bid=obs['focused_element_bid'],  # focused element bid
            screenshot=obs['screenshot'],  # base64-encoded screenshot, png
            url=obs['url'],  # URL of the page
            error=True if obs['last_action_error'] else False,  # error flag
            last_browser_action_error=obs[
                'last_action_error'
            ],  # last browser env action error
        )
    except Exception as e:
        return BrowserOutputObservation(
            content=str(e),
            screenshot='',
            error=True,
            last_browser_action_error=str(e),
            url=asked_url if action.action == ActionType.BROWSE else '',
        )
