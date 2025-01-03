import os

from openhands_aci.editor.exceptions import ToolError

from openhands.core.exceptions import BrowserUnavailableException
from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.runtime.browser.gui_use.gui_use import GUIUseTool
from openhands.runtime.browser.gui_use.types import ScalingSource
from openhands.runtime.browser.transformer import (
    translate_computer_use_action_to_browsergym_action,
)


async def browse(
    action: BrowseURLAction | BrowseInteractiveAction,
    browser: BrowserEnv | None,
    gui_use: GUIUseTool,
    last_obs: BrowserOutputObservation | None,
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
        _action_str = action.browser_actions

        if _action_str == 'gui_use':
            # received action_str defined by Anthropic's Computer Use feature: see https://docs.anthropic.com/en/docs/build-with-claude/computer-use#computer-tool
            extra_args = action.extra_args
            print(f'✅ extra_args: {extra_args}')

            try:
                validated_args = gui_use.validate_and_transform_args(
                    **(extra_args or {})
                )
            except ToolError as e:
                return BrowserOutputObservation(
                    content=f'ERROR:\n{e.message}',
                    screenshot='',
                    error=True,
                    last_browser_action_error=f'ERROR:\n{e.message}',
                    url=asked_url if action.action == ActionType.BROWSE else '',
                    trigger_by_action=action.action,
                )

            # construct a computer use action
            _action_str = f'{validated_args["action"]}('
            if validated_args.get('coordinate'):
                _action_str += f'coordinate={validated_args["coordinate"]}'
            if validated_args.get('text'):
                _action_str += f'text="{validated_args["text"]}"'
            _action_str += ')'

            # translate to BrowserGym actions
            # action in BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/functions.py
            action_str = translate_computer_use_action_to_browsergym_action(
                _action_str, last_obs
            )
        else:
            # received normal BrowserGym action
            action_str = _action_str
    else:
        raise ValueError(f'Invalid action type: {action.action}')

    try:
        # obs provided by BrowserGym: see
        # https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/env.py#L396
        obs = browser.step(action_str)
        mouse_position = obs.get('mouse_position', [0, 0])
        scaled_mouse_position = gui_use.scale_coordinates(
            ScalingSource.COMPUTER,
            int(mouse_position[0] or 0),
            int(mouse_position[1] or 0),
        )
        return BrowserOutputObservation(
            content=obs['text_content'],  # text content of the page
            url=obs.get('url', ''),  # URL of the page
            screenshot=gui_use.resize_image(
                obs.get('screenshot', None)
            ),  # base64-encoded screenshot, png
            open_pages_urls=obs.get('open_pages_urls', []),  # list of open pages
            active_page_index=obs.get(
                'active_page_index', -1
            ),  # index of the active page
            dom_object=obs.get('dom_object', {}),  # DOM object
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
            mouse_position=[scaled_mouse_position[0], scaled_mouse_position[1]],
        )
    except Exception as e:
        return BrowserOutputObservation(
            content=f'ERROR:\n{str(e)}',
            screenshot='',
            error=True,
            last_browser_action_error=f'ERROR:\n{str(e)}',
            url=asked_url if action.action == ActionType.BROWSE else '',
            trigger_by_action=action.action,
        )
