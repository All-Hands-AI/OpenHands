import os

from openhands.core.exceptions import BrowserUnavailableException
from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.utils.async_utils import call_sync_from_async


async def browse(
    action: BrowseURLAction | BrowseInteractiveAction, browser: BrowserEnv | None
) -> BrowserOutputObservation:
    if browser is None:
        raise BrowserUnavailableException()

    if isinstance(action, BrowseURLAction):
        # legacy BrowseURLAction
        asked_url = action.url
        if not asked_url.startswith('http'):
            asked_url = os.path.abspath(os.curdir) + action.url
        action_str = f'goto("{asked_url}")'

    elif isinstance(action, BrowseInteractiveAction):
        # new BrowseInteractiveAction, supports full featured BrowserGym actions
        # action in BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/functions.py
        action_str = action.browser_actions
    else:
        raise ValueError(f'Invalid action type: {action.action}')

    try:
        # obs provided by BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/env.py#L396
        obs = await call_sync_from_async(browser.step, action_str)
        if not isinstance(obs, dict):
            raise TypeError(f'Expected dict from browser.step, got {type(obs)}')

        return BrowserOutputObservation(
            content=str(obs.get('text_content', '')),  # text content of the page
            url=str(obs.get('url', '')),  # URL of the page
            screenshot=obs.get('screenshot', None),  # base64-encoded screenshot, png
            set_of_marks=obs.get(
                'set_of_marks', None
            ),  # base64-encoded Set-of-Marks annotated screenshot, png,
            goal_image_urls=list(obs.get('image_content', [])),
            open_pages_urls=list(obs.get('open_pages_urls', [])),  # list of open pages
            active_page_index=int(
                obs.get('active_page_index', -1)
            ),  # index of the active page
            dom_object=dict(obs.get('dom_object', {})),  # DOM object
            axtree_object=dict(
                obs.get('axtree_object', {})
            ),  # accessibility tree object
            extra_element_properties=dict(obs.get('extra_element_properties', {})),
            focused_element_bid=obs.get(
                'focused_element_bid', None
            ),  # focused element bid
            last_browser_action=str(
                obs.get('last_action', '')
            ),  # last browser env action performed
            last_browser_action_error=str(obs.get('last_action_error', '')),
            error=bool(obs.get('last_action_error', '')),  # error flag
            trigger_by_action=action.action,
        )
    except Exception as e:
        return BrowserOutputObservation(
            content=str(e),
            screenshot='',
            error=True,
            last_browser_action_error=str(e),
            url=asked_url if action.action == ActionType.BROWSE else '',
            trigger_by_action=action.action,
        )
