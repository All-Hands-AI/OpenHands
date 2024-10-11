import json
import os

import browsergym.core  # noqa F401 (we register the openended task as a gym environment)
import gymnasium as gym
from browsergym.utils.obs import flatten_dom_to_str

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.utils import (
    get_html_text_converter,
    image_to_png_base64_url,
)

BROWSER_EVAL_GET_GOAL_ACTION = 'GET_EVAL_GOAL'
BROWSER_EVAL_GET_REWARDS_ACTION = 'GET_EVAL_REWARDS'


class BrowserEnv:
    def __init__(self, browsergym_eval_env: str | None = None):
        self.html_text_converter = get_html_text_converter()
        self.eval_mode = bool(browsergym_eval_env)
        self.browsergym_eval_env = browsergym_eval_env
        self.env = self.init_browser()
        self.eval_goal = ''
        self.eval_rewards: list[float] = []

    def init_browser(self):
        if self.eval_mode:
            assert self.browsergym_eval_env is not None
            logger.info('Initializing browser env for web browsing evaluation.')
            if 'webarena' in self.browsergym_eval_env:
                import browsergym.webarena  # noqa F401 register webarena tasks as gym environments
            elif 'miniwob' in self.browsergym_eval_env:
                import browsergym.miniwob  # noqa F401 register miniwob tasks as gym environments
            else:
                raise ValueError(
                    f'Unsupported browsergym eval env: {self.browsergym_eval_env}'
                )
            env = gym.make(self.browsergym_eval_env)
        else:
            env = gym.make(
                'browsergym/openended',
                task_kwargs={'start_url': 'about:blank', 'goal': 'PLACEHOLDER_GOAL'},
                wait_for_user_message=False,
                headless=True,
                disable_env_checker=True,
            )

        obs, info = env.reset()
        if self.eval_mode:
            logger.info(f"Browsing goal: {obs['goal']}")
            self.eval_goal = obs['goal']

        logger.info('Browser env started.')
        return env

    def _execute_browsergym_action(self, action: str) -> BrowserOutputObservation:
        """Execute an action in the BrowserGym environment and return the BrowserOutputObservation."""
        # OpenHands reserved action for evaluation
        if action == BROWSER_EVAL_GET_GOAL_ACTION:
            assert (
                self.eval_goal
            ), 'Eval mode is not enabled to execute get goal action.'
            return BrowserOutputObservation(
                content=self.eval_goal,
                url='',
                screenshot='',
            )
        elif action == BROWSER_EVAL_GET_REWARDS_ACTION:
            assert (
                self.eval_mode
            ), 'Eval mode is not enabled to execute get rewards action.'
            return BrowserOutputObservation(
                content=json.dumps(self.eval_rewards),
                url='',
                screenshot='',
            )

        # obs provided by BrowserGym: see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/env.py#L396
        obs, reward, terminated, truncated, info = self.env.step({'action': action})
        if self.eval_mode:
            self.eval_rewards.append(reward)

        # Process observation
        html_str = flatten_dom_to_str(obs['dom_object'])
        return BrowserOutputObservation(
            content=self.html_text_converter.handle(
                html_str
            ),  # text content of the page
            url=obs.get('url', ''),  # URL of the page
            screenshot=image_to_png_base64_url(obs['screenshot']),
            open_pages_urls=obs.get('open_pages_urls', []),  # list of open pages
            active_page_index=obs['active_page_index'].item(),
            dom_object=obs.get('dom_object', {}),  # DOM object
            axtree_object=obs.get('axtree_object', {}),  # accessibility tree object
            extra_element_properties=obs.get('extra_element_properties', {}),
            focused_element_bid=obs.get('focused_element_bid', None),
            last_browser_action=obs.get('last_action', ''),
            last_browser_action_error=obs.get('last_action_error', ''),
            error=True if obs.get('last_action_error', '') else False,
        )

    def execute(
        self, action: BrowseURLAction | BrowseInteractiveAction
    ) -> BrowserOutputObservation:
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
            obs: BrowserOutputObservation = self._execute_browsergym_action(action_str)
            return obs
        except Exception as e:
            logger.error(f'Error executing action in BrowserEnv: {e}', exc_info=True)
            return BrowserOutputObservation(
                content=str(e),
                screenshot='',
                error=True,
                last_browser_action_error=str(e),
                url=asked_url if action.action == ActionType.BROWSE else '',
            )

    def close(self):
        if self.env:
            self.env.close()
