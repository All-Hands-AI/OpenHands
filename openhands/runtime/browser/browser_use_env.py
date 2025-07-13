"""
Browser-Use environment implementation for OpenHands.

This module provides a Browser-Use-based implementation that maintains compatibility
with the existing BrowserGym interface while using Browser-Use under the hood.
"""

import asyncio
import atexit
import json
import multiprocessing
import time
import uuid
from typing import Any, Dict, Optional

from browser_use import BrowserSession, Controller
from openhands.core.exceptions import BrowserInitException
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.browser.action_mapper import ActionMapper
from openhands.runtime.browser.observation_adapter import ObservationAdapter
from openhands.utils.shutdown_listener import should_continue, should_exit


BROWSER_EVAL_GET_GOAL_ACTION = 'GET_EVAL_GOAL'
BROWSER_EVAL_GET_REWARDS_ACTION = 'GET_EVAL_REWARDS'


class BrowserUseEnv:
    """Browser environment using Browser-Use library instead of BrowserGym."""

    def __init__(self, browser_use_config: Optional[str] = None):
        """
        Initialize Browser-Use environment.

        Args:
            browser_use_config: Configuration string for Browser-Use (for future use)
        """
        self.browser_use_config = browser_use_config
        self.eval_mode = False
        self.eval_dir = ''
        self.eval_goal = None
        self.goal_image_urls = []
        self.eval_rewards = []

        # Initialize browser environment process
        multiprocessing.set_start_method('spawn', force=True)
        self.browser_side, self.agent_side = multiprocessing.Pipe()

        self.init_browser()
        atexit.register(self.close)

    def init_browser(self) -> None:
        """Initialize the browser environment."""
        logger.debug('Starting Browser-Use environment...')
        try:
            self.process = multiprocessing.Process(target=self.browser_process)
            self.process.start()
        except Exception as e:
            logger.error(f'Failed to start browser process: {e}')
            raise

        if not self.check_alive(timeout=200):
            self.close()
            raise BrowserInitException('Failed to start browser environment.')

    def browser_process(self) -> None:
        """Browser process that handles Browser-Use operations."""
        logger.info('Initializing Browser-Use environment.')

        try:
            # Initialize Browser-Use session
            browser_session = BrowserSession()
            controller = Controller()

            # Start the browser
            browser_session.start()

            # Navigate to a blank page initially
            browser_session.navigate_to('about:blank')

            logger.info('Browser-Use environment started successfully.')

            while should_continue():
                try:
                    if self.browser_side.poll(timeout=0.01):
                        unique_request_id, action_data = self.browser_side.recv()

                        # Handle shutdown
                        if unique_request_id == 'SHUTDOWN':
                            logger.debug('SHUTDOWN received, shutting down browser env...')
                            browser_session.close()
                            return
                        elif unique_request_id == 'IS_ALIVE':
                            self.browser_side.send(('ALIVE', None))
                            continue

                        # Handle evaluation actions
                        if action_data['action'] == BROWSER_EVAL_GET_GOAL_ACTION:
                            self.browser_side.send(
                                (
                                    unique_request_id,
                                    {
                                        'text_content': self.eval_goal,
                                        'image_content': self.goal_image_urls,
                                    },
                                )
                            )
                            continue
                        elif action_data['action'] == BROWSER_EVAL_GET_REWARDS_ACTION:
                            self.browser_side.send(
                                (
                                    unique_request_id,
                                    {'text_content': json.dumps(self.eval_rewards)},
                                )
                            )
                            continue

                        # Execute browser action
                        action_str = action_data['action']
                        obs = self.execute_action(browser_session, controller, action_str)

                        # Save rewards for evaluation
                        if self.eval_mode:
                            # Browser-Use doesn't have built-in rewards like BrowserGym
                            # We'll use a simple success indicator for now
                            reward = 1.0 if not obs.get('error', False) else 0.0
                            self.eval_rewards.append(reward)

                        self.browser_side.send((unique_request_id, obs))

                except KeyboardInterrupt:
                    logger.debug('Browser env process interrupted by user.')
                    try:
                        browser_session.close()
                    except Exception:
                        pass
                    return

        except Exception as e:
            logger.error(f'Error in browser process: {e}')
            raise

    def execute_action(
        self,
        browser_session: BrowserSession,
        controller: Controller,
        action_str: str
    ) -> Dict[str, Any]:
        """
        Execute a browser action using Browser-Use.

        Args:
            browser_session: Browser-Use browser session
            controller: Browser-Use controller
            action_str: Action string to execute

        Returns:
            Observation dictionary in OpenHands format
        """
        try:
            # Parse action using action mapper
            action_mapper = ActionMapper()
            browser_use_action = action_mapper.parse_action(action_str)

            if browser_use_action is None:
                # Handle unsupported actions
                return {
                    'url': '',
                    'screenshot': '',
                    'text_content': '',
                    'dom_object': {},
                    'axtree_object': {},
                    'extra_element_properties': {},
                    'open_pages_urls': [],
                    'active_page_index': 0,
                    'last_action': action_str,
                    'last_action_error': f'Unsupported action: {action_str}',
                    'error': True,
                }

            # Execute action using controller
            result = controller.act(browser_session, browser_use_action)

            # Create observation using adapter
            observation_adapter = ObservationAdapter()

            # Note: We need to handle async operations properly
            # For now, we'll create a simple observation
            current_page = browser_session.get_current_page()
            url = current_page.url if current_page else ''

            # Take screenshot
            screenshot_data = browser_session.take_screenshot()
            screenshot = ''
            if screenshot_data:
                if isinstance(screenshot_data, bytes):
                    import base64
                    screenshot = f"data:image/png;base64,{base64.b64encode(screenshot_data).decode()}"
                elif isinstance(screenshot_data, str):
                    screenshot = screenshot_data

            # Get page HTML
            html_content = browser_session.get_page_html() or ''

            # Get tabs info
            tabs_info = browser_session.get_tabs_info()
            open_pages_urls = [tab.get('url', '') for tab in tabs_info] if tabs_info else []

            # Create observation
            obs = {
                'url': url,
                'screenshot': screenshot,
                'text_content': html_content,
                'dom_object': {},
                'axtree_object': {},
                'extra_element_properties': {},
                'open_pages_urls': open_pages_urls,
                'active_page_index': 0,
                'last_action': action_str,
                'last_action_error': '',
                'error': False,
            }

            return obs

        except Exception as e:
            logger.error(f'Error executing action {action_str}: {e}')
            return {
                'url': '',
                'screenshot': '',
                'text_content': '',
                'dom_object': {},
                'axtree_object': {},
                'extra_element_properties': {},
                'open_pages_urls': [],
                'active_page_index': 0,
                'last_action': action_str,
                'last_action_error': str(e),
                'error': True,
            }

    def step(self, action_str: str, timeout: float = 120) -> Dict[str, Any]:
        """
        Execute an action in the browser environment and return the observation.

        This method maintains compatibility with the original BrowserGym interface.

        Args:
            action_str: Action string to execute
            timeout: Timeout for the operation

        Returns:
            Observation dictionary
        """
        unique_request_id = str(uuid.uuid4())
        self.agent_side.send((unique_request_id, {'action': action_str}))
        start_time = time.time()

        while True:
            if should_exit() or time.time() - start_time > timeout:
                raise TimeoutError('Browser environment took too long to respond.')

            if self.agent_side.poll(timeout=0.01):
                response_id, obs = self.agent_side.recv()
                if response_id == unique_request_id:
                    return dict(obs)

    def check_alive(self, timeout: float = 60) -> bool:
        """Check if the browser environment is alive."""
        self.agent_side.send(('IS_ALIVE', None))
        if self.agent_side.poll(timeout=timeout):
            response_id, _ = self.agent_side.recv()
            if response_id == 'ALIVE':
                return True
            logger.debug(f'Browser env is not alive. Response ID: {response_id}')
        return False

    def close(self) -> None:
        """Close the browser environment."""
        if not self.process.is_alive():
            return
        try:
            self.agent_side.send(('SHUTDOWN', None))
            self.process.join(5)  # Wait for the process to terminate
            if self.process.is_alive():
                logger.error(
                    'Browser process did not terminate, forcefully terminating...'
                )
                self.process.terminate()
                self.process.join(5)  # Wait for the process to terminate
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join(5)  # Wait for the process to terminate
            self.agent_side.close()
            self.browser_side.close()
        except Exception as e:
            logger.error(f'Encountered an error when closing browser env: {e}')
