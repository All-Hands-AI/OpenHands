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

        # Check text_content type - this should be required as in the main branch
        if not isinstance(obs['text_content'], str):
            raise TypeError(
                f"Expected 'text_content' to be str, got {type(obs['text_content'])}"
            )
        text_content = obs['text_content']

        # Check URL type
        if 'url' in obs:
            if not isinstance(obs['url'], str):
                raise TypeError(f"Expected 'url' to be str, got {type(obs['url'])}")
            url = obs['url']
        else:
            url = ''

        # Check image_content type
        if 'image_content' in obs:
            if not isinstance(obs['image_content'], list):
                raise TypeError(
                    f"Expected 'image_content' to be list, got {type(obs['image_content'])}"
                )
            image_content = obs['image_content']
        else:
            image_content = []

        # Check open_pages_urls type
        if 'open_pages_urls' in obs:
            if not isinstance(obs['open_pages_urls'], list):
                raise TypeError(
                    f"Expected 'open_pages_urls' to be list, got {type(obs['open_pages_urls'])}"
                )
            open_pages_urls = obs['open_pages_urls']
        else:
            open_pages_urls = []

        # Check active_page_index type
        if 'active_page_index' in obs:
            if not isinstance(obs['active_page_index'], int):
                raise TypeError(
                    f"Expected 'active_page_index' to be int, got {type(obs['active_page_index'])}"
                )
            active_page_index = obs['active_page_index']
        else:
            active_page_index = -1

        # Check dom_object type
        if 'dom_object' in obs:
            if not isinstance(obs['dom_object'], dict):
                raise TypeError(
                    f"Expected 'dom_object' to be dict, got {type(obs['dom_object'])}"
                )
            dom_object = obs['dom_object']
        else:
            dom_object = {}

        # Check axtree_object type
        if 'axtree_object' in obs:
            if not isinstance(obs['axtree_object'], dict):
                raise TypeError(
                    f"Expected 'axtree_object' to be dict, got {type(obs['axtree_object'])}"
                )
            axtree_object = obs['axtree_object']
        else:
            axtree_object = {}

        # Check extra_element_properties type
        if 'extra_element_properties' in obs:
            if not isinstance(obs['extra_element_properties'], dict):
                raise TypeError(
                    f"Expected 'extra_element_properties' to be dict, got {type(obs['extra_element_properties'])}"
                )
            extra_element_properties = obs['extra_element_properties']
        else:
            extra_element_properties = {}

        # Check last_action type
        if 'last_action' in obs:
            if not isinstance(obs['last_action'], str):
                raise TypeError(
                    f"Expected 'last_action' to be str, got {type(obs['last_action'])}"
                )
            last_action = obs['last_action']
        else:
            last_action = ''

        # Check last_action_error type
        if 'last_action_error' in obs:
            if not isinstance(obs['last_action_error'], str):
                raise TypeError(
                    f"Expected 'last_action_error' to be str, got {type(obs['last_action_error'])}"
                )
            last_action_error = obs['last_action_error']
        else:
            last_action_error = ''

        # Determine error flag based on presence of last_action_error
        error_flag = bool(last_action_error)

        return BrowserOutputObservation(
            content=text_content,  # text content of the page
            url=url,  # URL of the page
            screenshot=obs.get('screenshot', None),  # base64-encoded screenshot, png
            set_of_marks=obs.get(
                'set_of_marks', None
            ),  # base64-encoded Set-of-Marks annotated screenshot, png,
            goal_image_urls=image_content,
            open_pages_urls=open_pages_urls,  # list of open pages
            active_page_index=active_page_index,  # index of the active page
            dom_object=dom_object,  # DOM object
            axtree_object=axtree_object,  # accessibility tree object
            extra_element_properties=extra_element_properties,
            focused_element_bid=obs.get(
                'focused_element_bid', None
            ),  # focused element bid
            last_browser_action=last_action,  # last browser env action performed
            last_browser_action_error=last_action_error,
            error=error_flag,  # error flag
            trigger_by_action=action.action,
        )
    except Exception as e:
        error_message = str(e)
        url_value = asked_url if action.action == ActionType.BROWSE else ''

        return BrowserOutputObservation(
            content=error_message,
            screenshot='',
            error=True,
            last_browser_action_error=error_message,
            url=url_value,
            trigger_by_action=action.action,
        )
