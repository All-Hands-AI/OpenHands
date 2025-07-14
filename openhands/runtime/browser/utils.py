import base64
import datetime
import os
from pathlib import Path
from typing import Any

from browsergym.utils.obs import flatten_axtree_to_str
from PIL import Image

from openhands.core.exceptions import BrowserUnavailableException
from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.base64 import png_base64_url_to_image
from openhands.runtime.browser.browser_use_env import BrowserUseEnv
from openhands.utils.async_utils import call_sync_from_async


def get_axtree_str(
    axtree_object: dict[str, Any],
    extra_element_properties: dict[str, Any],
    filter_visible_only: bool = False,
) -> str:
    """Get accessibility tree as string."""
    try:
        # Try to use browsergym's flatten_axtree_to_str if available
        from browsergym.utils.obs import flatten_axtree_to_str
        cur_axtree_txt = flatten_axtree_to_str(
            axtree_object,
            extra_properties=extra_element_properties,
            with_clickable=True,
            skip_generic=False,
            filter_visible_only=filter_visible_only,
        )
        return str(cur_axtree_txt)
    except ImportError:
        # Fallback when browsergym is not available
        return _simple_axtree_to_str(axtree_object, extra_element_properties, filter_visible_only)
    except Exception as e:
        # Fallback when browsergym fails
        return f"[Error processing accessibility tree: {e}]\n{_simple_axtree_to_str(axtree_object, extra_element_properties, filter_visible_only)}"


def _simple_axtree_to_str(
    axtree_object: dict[str, Any],
    extra_element_properties: dict[str, Any],
    filter_visible_only: bool = False,
) -> str:
    """Simple accessibility tree to string conversion."""
    if not axtree_object:
        return "[No accessibility tree available]"

    result = []

    def traverse_node(node, level=0):
        if not isinstance(node, dict):
            return

        # Extract basic information
        bid = node.get('bid', '')
        tag = node.get('tag', '')
        text = node.get('text', '')
        visible = node.get('visible', True)

        # Skip invisible elements if filtering
        if filter_visible_only and not visible:
            return

        # Create line with proper indentation
        indent = '  ' * level
        line = f'{indent}[{bid}] {tag}'
        if text:
            line += f' "{text}"'

        result.append(line)

        # Traverse children
        children = node.get('children', [])
        for child in children:
            traverse_node(child, level + 1)

    # Start traversal from root
    if isinstance(axtree_object, dict):
        traverse_node(axtree_object)
    elif isinstance(axtree_object, list):
        for node in axtree_object:
            traverse_node(node)

    return '\n'.join(result) if result else "[Empty accessibility tree]"


def get_agent_obs_text(obs: BrowserOutputObservation) -> str:
    """Get a concise text that will be shown to the agent."""
    if obs.trigger_by_action == ActionType.BROWSE_INTERACTIVE:
        text = f'[Current URL: {obs.url}]\n'
        text += f'[Focused element bid: {obs.focused_element_bid}]\n'

        # Add screenshot path information if available
        if obs.screenshot_path:
            text += f'[Screenshot saved to: {obs.screenshot_path}]\n'

        text += '\n'

        if obs.error:
            text += (
                '================ BEGIN error message ===============\n'
                'The following error occurred when executing the last action:\n'
                f'{obs.last_browser_action_error}\n'
                '================ END error message ===============\n'
            )
        else:
            text += '[Action executed successfully.]\n'

        # Try to get accessibility tree
        axtree_available = False
        cur_axtree_txt = ''
        try:
            cur_axtree_txt = get_axtree_str(
                obs.axtree_object,
                obs.extra_element_properties,
                filter_visible_only=obs.filter_visible_only,
            )
            # Check if we got a meaningful accessibility tree
            if cur_axtree_txt and not cur_axtree_txt.startswith('[No accessibility tree available]') and not cur_axtree_txt.startswith('[Empty accessibility tree]') and not cur_axtree_txt.startswith('[Error processing accessibility tree'):
                axtree_available = True
                if not obs.filter_visible_only:
                    text += (
                        f'Accessibility tree of the COMPLETE webpage:\nNote: [bid] is the unique alpha-numeric identifier at the beginning of lines for each element in the AXTree. Always use bid to refer to elements in your actions.\n'
                        f'============== BEGIN accessibility tree ==============\n'
                        f'{cur_axtree_txt}\n'
                        f'============== END accessibility tree ==============\n'
                    )
                else:
                    text += (
                        f'Accessibility tree of the VISIBLE portion of the webpage (accessibility tree of complete webpage is too large and you may need to scroll to view remaining portion of the webpage):\nNote: [bid] is the unique alpha-numeric identifier at the beginning of lines for each element in the AXTree. Always use bid to refer to elements in your actions.\n'
                        f'============== BEGIN accessibility tree ==============\n'
                        f'{cur_axtree_txt}\n'
                        f'============== END accessibility tree ==============\n'
                    )
        except Exception as e:
            text += f'\n[Error encountered when processing the accessibility tree: {e}]'

        # If accessibility tree is not available, empty, or errored, show the page content instead
        if not axtree_available:
            text += '============== BEGIN webpage content ==============\n'
            text += obs.content
            text += '\n============== END webpage content ==============\n'

        return text

    elif obs.trigger_by_action == ActionType.BROWSE:
        text = f'[Current URL: {obs.url}]\n'

        if obs.error:
            text += (
                '================ BEGIN error message ===============\n'
                'The following error occurred when trying to visit the URL:\n'
                f'{obs.last_browser_action_error}\n'
                '================ END error message ===============\n'
            )
        text += '============== BEGIN webpage content ==============\n'
        text += obs.content
        text += '\n============== END webpage content ==============\n'
        return text
    else:
        raise ValueError(f'Invalid trigger_by_action: {obs.trigger_by_action}')


async def browse(
    action: BrowseURLAction | BrowseInteractiveAction,
    browser: BrowserUseEnv | None,
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

        # Create the observation with all data
        observation = BrowserOutputObservation(
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

        # Process the content first using the axtree_object
        observation.content = get_agent_obs_text(observation)

        # If return_axtree is False, remove the axtree_object to save space
        if not action.return_axtree:
            observation.dom_object = {}
            observation.axtree_object = {}
            observation.extra_element_properties = {}

        return observation
    except Exception as e:
        error_message = str(e)
        error_url = asked_url if action.action == ActionType.BROWSE else ''

        # Create error observation
        observation = BrowserOutputObservation(
            content=error_message,
            screenshot='',
            screenshot_path=None,
            error=True,
            last_browser_action_error=error_message,
            url=error_url,
            trigger_by_action=action.action,
        )

        # Process the content using get_agent_obs_text regardless of return_axtree value
        try:
            observation.content = get_agent_obs_text(observation)
        except Exception:
            # If get_agent_obs_text fails, keep the original error message
            pass

        return observation
