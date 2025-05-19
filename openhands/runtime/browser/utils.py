import base64
import datetime
import os
from pathlib import Path

from PIL import Image

from openhands.core.exceptions import BrowserUnavailableException
from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.base64 import png_base64_url_to_image
from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.utils.async_utils import call_sync_from_async


async def browse(
    action: BrowseURLAction | BrowseInteractiveAction,
    browser: BrowserEnv | None,
    workspace_dir: str | None = None,
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

        # Save screenshot if workspace_dir is provided
        screenshot_path = None
        if workspace_dir is not None and obs.get('screenshot'):
            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path(workspace_dir) / '.browser_screenshots'
            screenshots_dir.mkdir(exist_ok=True)

            # Generate a filename based on timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            screenshot_filename = f'screenshot_{timestamp}.png'
            screenshot_path = str(screenshots_dir / screenshot_filename)

            # Direct image saving from base64 data without using PIL's Image.open
            # This approach bypasses potential encoding issues that might occur when
            # converting between different image representations, ensuring the raw PNG
            # data from the browser is saved directly to disk.

            # Extract the base64 data
            base64_data = obs.get('screenshot', '')
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            try:
                # Decode base64 directly to binary
                image_data = base64.b64decode(base64_data)

                # Write binary data directly to file
                with open(screenshot_path, 'wb') as f:
                    f.write(image_data)

                # Verify the image was saved correctly by opening it
                # This is just a verification step and can be removed in production
                Image.open(screenshot_path).verify()
            except Exception:
                # If direct saving fails, fall back to the original method
                image = png_base64_url_to_image(obs.get('screenshot'))
                image.save(screenshot_path, format='PNG', optimize=True)

        return BrowserOutputObservation(
            content=obs['text_content'],  # text content of the page
            url=obs.get('url', ''),  # URL of the page
            screenshot=obs.get('screenshot', None),  # base64-encoded screenshot, png
            screenshot_path=screenshot_path,  # path to saved screenshot file
            set_of_marks=obs.get(
                'set_of_marks', None
            ),  # base64-encoded Set-of-Marks annotated screenshot, png,
            goal_image_urls=obs.get('image_content', []),
            open_pages_urls=obs.get('open_pages_urls', []),  # list of open pages
            active_page_index=obs.get(
                'active_page_index', -1
            ),  # index of the active page
            axtree_object=obs.get('axtree_object', {}),  # accessibility tree object
            extra_element_properties=obs.get('extra_element_properties', {}),
            focused_element_bid=obs.get(
                'focused_element_bid', None
            ),  # focused element bid
            last_browser_action=obs.get(
                'last_action', ''
            ),  # last browser env action performed
            last_browser_action_error=obs.get('last_action_error', ''),
            error=True if obs.get('last_action_error', '') else False,  # error flag
            trigger_by_action=action.action,
        )
    except Exception as e:
        return BrowserOutputObservation(
            content=str(e),
            screenshot='',
            screenshot_path=None,
            error=True,
            last_browser_action_error=str(e),
            url=asked_url if action.action == ActionType.BROWSE else '',
            trigger_by_action=action.action,
        )
