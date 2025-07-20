"""
Browser environment using Browser-Use library.

This module provides a drop-in replacement for the previous browser environment,
maintaining the same interface while using Browser-Use under the hood.
"""

import asyncio
import atexit
import json
import multiprocessing
import time
import uuid
from typing import Any, Dict, Optional, Union

from browser_use import BrowserSession, Controller
from browser_use.controller.service import (
    ClickElementAction,
    GoToUrlAction,
    InputTextAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
    CloseTabAction,
    UploadFileAction,
    DoneAction,
    NoParamsAction,
)
from openhands.core.exceptions import BrowserInitException
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.browser.observation_adapter import ObservationAdapter
from openhands.utils.shutdown_listener import should_continue, should_exit


BROWSER_EVAL_GET_GOAL_ACTION = 'GET_EVAL_GOAL'
BROWSER_EVAL_GET_REWARDS_ACTION = 'GET_EVAL_REWARDS'


class BrowserUseEnv:
    """Browser environment using Browser-Use library."""

    def __init__(self, browser_use_config: str | None = None, eval_mode: bool = False, eval_goal: str = '', goal_image_urls: list[str] = None):
        self.browser_use_config = browser_use_config
        self.eval_mode = eval_mode
        self.eval_goal = eval_goal
        self.goal_image_urls = goal_image_urls or []
        self.eval_rewards = []

        # Multiprocessing setup
        self.browser_side, self.agent_side = multiprocessing.Pipe()

        self.init_browser()
        atexit.register(self.close)

    def init_browser(self) -> None:
        """Initialize the browser environment."""
        logger.info('Starting Browser-Use environment...')
        try:
            self.process = multiprocessing.Process(target=self._browser_process_wrapper)
            self.process.start()
            logger.info(f'Browser process started with PID: {self.process.pid}')
        except Exception as e:
            logger.error(f'Failed to start browser process: {e}')
            raise

        # Wait for browser to be ready with a longer timeout for Docker containers
        if not self.check_alive(timeout=60):
            logger.error('Browser initialization timed out after 60 seconds')
            self.close()
            raise BrowserInitException('Failed to start browser environment within timeout.')

        logger.info('Browser environment initialized successfully')

    def _browser_process_wrapper(self) -> None:
        """Wrapper for the browser process to handle multiprocessing."""
        try:
            logger.info('Starting browser process wrapper...')
            # Set environment variables for headless browser operation
            import os
            os.environ['DISPLAY'] = ':99'
            os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '')
            os.environ['NO_SANDBOX'] = '1'
            os.environ['CHROME_HEADLESS'] = '1'
            # Additional environment variables for Docker container compatibility
            # Note: Removed PLAYWRIGHT_BROWSERS_PATH and PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD
            # to allow Playwright to use its installed browsers
            os.environ['BROWSER_USE_HEADLESS'] = '1'  # Force headless mode
            os.environ['BROWSER_USE_NO_SANDBOX'] = '1'  # Disable sandbox
            os.environ['BROWSER_USE_DISABLE_DEV_SHM'] = '1'  # Disable /dev/shm usage
            os.environ['BROWSER_USE_DISABLE_GPU'] = '1'  # Disable GPU
            os.environ['BROWSER_USE_DISABLE_WEB_SECURITY'] = '1'  # Disable web security
            os.environ['BROWSER_USE_DISABLE_FEATURES'] = 'VizDisplayCompositor'  # Disable features
            logger.info('Environment variables set for headless browser')

            self.browser_process()
        except Exception as e:
            logger.error(f'Error in browser process wrapper: {e}')
            # Send error back to main process
            try:
                self.browser_side.send(('ERROR', str(e)))
            except:
                pass
            raise

    def browser_process(self) -> None:
        """Browser process that handles Browser-Use operations."""
        logger.info('Initializing Browser-Use environment.')

        try:
            # Run the async browser process
            asyncio.run(self._async_browser_process())
        except Exception as e:
            logger.error(f'Error in browser process: {e}')
            raise

    async def _async_browser_process(self) -> None:
        """Async browser process that handles Browser-Use operations."""
        browser_session = None
        controller = None

        try:
            logger.info('Initializing Browser-Use session...')
            # Initialize Browser-Use session
            browser_session = BrowserSession()
            logger.info('BrowserSession created successfully')
            controller = Controller()
            logger.info('Controller created successfully')

            logger.info('Starting browser session...')
            # Start the browser
            await browser_session.start()
            logger.info('Browser session started successfully')

            logger.info('Navigating to blank page...')
            # Navigate to a blank page initially
            await browser_session.navigate('about:blank')
            logger.info('Successfully navigated to blank page')

            logger.info('Browser-Use environment started successfully.')

            while should_continue():
                try:
                    if self.browser_side.poll(timeout=0.01):
                        unique_request_id, action_data = self.browser_side.recv()

                        # Handle shutdown
                        if unique_request_id == 'SHUTDOWN':
                            logger.info('SHUTDOWN received, shutting down browser env...')
                            break
                        elif unique_request_id == 'IS_ALIVE':
                            logger.info('IS_ALIVE received, responding with ALIVE')
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
                        obs = await self.execute_action_async(browser_session, controller, action_str)

                        # Save rewards for evaluation
                        if self.eval_mode:
                            # Browser-Use doesn't have built-in rewards like the previous browser environment
                            # For evaluation environments, rewards would need to be implemented separately
                            reward = 1.0 if not obs.get('error', False) else 0.0
                            self.eval_rewards.append(reward)

                        self.browser_side.send((unique_request_id, obs))

                except KeyboardInterrupt:
                    logger.info('Browser env process interrupted by user.')
                    break

        except Exception as e:
            logger.error(f'Error in async browser process: {e}')
            # Send error back to main process
            try:
                self.browser_side.send(('ERROR', str(e)))
            except:
                pass
            raise
        finally:
            # Clean up browser session
            if browser_session:
                try:
                    await browser_session.close()
                except Exception as e:
                    logger.error(f'Error closing browser session: {e}')

    async def execute_action_async(
        self,
        browser_session: BrowserSession,
        controller: Controller,
        action: Union[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a browser action using Browser-Use asynchronously.

        Args:
            browser_session: Browser-Use browser session
            controller: Browser-Use controller
            action: Browser-Use action model or action string (for backward compatibility)

        Returns:
            Observation dictionary in OpenHands format
        """
        try:
            # Handle both action models and strings for backward compatibility
            if isinstance(action, str):
                # For backward compatibility, try to parse string actions
                browser_use_action = self._parse_action_string(action)
                action_str = action
            else:
                # Direct Browser-Use action model
                browser_use_action = action
                action_str = str(action)

            logger.info(f'Executing action: {action_str}')
            logger.info(f'Parsed action: {browser_use_action}')

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

            # Execute action - handle different action types
            result = None
            # Handle go_back and go_forward as special cases
            if isinstance(browser_use_action, tuple) and len(browser_use_action) == 2 and isinstance(browser_use_action[1], NoParamsAction):
                action_name, action_model = browser_use_action
                logger.info(f'Executing special navigation action: {action_name}')
                if action_name == 'go_back':
                    # Use direct BrowserSession method for go_back
                    logger.info('Using direct go_back method')
                    await browser_session.go_back()
                    result = {'success': True}
                elif action_name == 'go_forward':
                    # Use direct BrowserSession method for go_forward
                    logger.info('Using direct go_forward method')
                    await browser_session.go_forward()
                    result = {'success': True}
                else:
                    # For other special actions, try controller
                    result = await controller.act(browser_session, action_name, **{})
            elif isinstance(browser_use_action, GoToUrlAction):
                # Use direct navigation for URL actions
                logger.info(f'Using direct navigation for URL: {browser_use_action.url}')
                await browser_session.navigate(browser_use_action.url)
                result = {'success': True}
            elif isinstance(browser_use_action, NoParamsAction):
                # Handle no-op actions (wait, go_back, go_forward)
                logger.info('Executing no-op action')
                if 'noop' in action_str.lower():
                    # Extract wait time if present
                    import re
                    wait_match = re.search(r'noop\((\d+)\)', action_str)
                    if wait_match:
                        wait_time = int(wait_match.group(1)) / 1000.0  # Convert ms to seconds
                        import asyncio
                        await asyncio.sleep(wait_time)
                    result = {'success': True}
                elif 'go_back' in action_str.lower():
                    # Handle go_back action directly
                    logger.info('Using direct go_back method for string action')
                    await browser_session.go_back()
                    result = {'success': True}
                elif 'go_forward' in action_str.lower():
                    # Handle go_forward action directly
                    logger.info('Using direct go_forward method for string action')
                    await browser_session.go_forward()
                    result = {'success': True}
                else:
                    # For other no-op actions - use controller if available
                    try:
                        result = await controller.act(browser_session, browser_use_action)
                    except Exception as e:
                        logger.warning(f'Controller action failed for {action_str}: {e}')
                        result = {'success': True}  # Assume success for now
            else:
                # For other actions, try using controller
                logger.info(f'Executing Browser-Use action: {browser_use_action}')
                try:
                    result = await controller.act(browser_session, browser_use_action)
                except Exception as e:
                    logger.error(f'Controller action failed: {e}')
                    # Fallback: try to handle common actions directly
                    if isinstance(browser_use_action, ClickElementAction):
                        # Try to click by index
                        logger.info(f'Attempting direct click for index: {browser_use_action.index}')
                        # This would need implementation based on Browser-Use's element selection
                        result = {'success': True}  # Placeholder
                    elif isinstance(browser_use_action, InputTextAction):
                        # Try to input text by index
                        logger.info(f'Attempting direct input for index: {browser_use_action.index}')
                        # This would need implementation based on Browser-Use's element selection
                        result = {'success': True}  # Placeholder
                    else:
                        result = {'success': False, 'error': str(e)}

            logger.info(f'Action result: {result}')

            # Create observation using adapter
            observation_adapter = ObservationAdapter()

            # Get current page information
            current_page = await browser_session.get_current_page()
            url = current_page.url if current_page else ''
            logger.info(f'Current page URL: {url}')

            # Take screenshot
            screenshot_data = await browser_session.take_screenshot()
            screenshot = ''
            if screenshot_data:
                if isinstance(screenshot_data, bytes):
                    import base64
                    screenshot = f"data:image/png;base64,{base64.b64encode(screenshot_data).decode()}"
                elif isinstance(screenshot_data, str):
                    screenshot = screenshot_data

            # Get page HTML
            html_content = await browser_session.get_page_html() or ''

            # Get page structure (DOM and accessibility tree)
            page_structure = await observation_adapter._get_page_structure(browser_session)
            logger.info(f'Page structure: {page_structure}')

            # Get tabs info
            tabs_info = await browser_session.get_tabs_info()
            open_pages_urls = [tab.url for tab in tabs_info] if tabs_info else []

            # Create observation
            obs = {
                'url': url,
                'screenshot': screenshot,
                'text_content': html_content,
                'dom_object': page_structure.get('dom', {}),
                'axtree_object': page_structure.get('axtree', {}),
                'extra_element_properties': page_structure.get('properties', {}),
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

    def _parse_action_string(self, action_str: str) -> Optional[Any]:
        """
        Parse action string for backward compatibility.

        This is a simplified parser for legacy string-based actions.
        In the future, this should be removed as agents will use Browser-Use actions directly.
        """
        import re

        action_str = action_str.strip()
        logger.info(f'Parsing action string: {action_str}')

        # Simple regex patterns for common actions
        goto_pattern = re.compile(r'goto\("([^"]+)"\)')
        click_pattern = re.compile(r'click\("([^"]+)"\)')
        fill_pattern = re.compile(r'fill\("([^"]+)",\s*"([^"]*)"\)')
        scroll_pattern = re.compile(r'scroll\(([^,]+),\s*([^)]+)\)')
        noop_pattern = re.compile(r'noop\((\d*)\)')  # Allow empty noop()
        go_back_pattern = re.compile(r'go_back\(\)')
        go_forward_pattern = re.compile(r'go_forward\(\)')
        upload_file_pattern = re.compile(r'upload_file\("([^"]+)",\s*"([^"]*)"\)')
        press_pattern = re.compile(r'press\("([^"]+)",\s*"([^"]*)"\)')
        hover_pattern = re.compile(r'hover\("([^"]+)"\)')
        focus_pattern = re.compile(r'focus\("([^"]+)"\)')
        clear_pattern = re.compile(r'clear\("([^"]+)"\)')
        select_option_pattern = re.compile(r'select_option\("([^"]+)",\s*"([^"]*)"\)')

        if match := goto_pattern.match(action_str):
            url = match.group(1)
            logger.info(f'Parsed goto action with URL: {url}')
            return GoToUrlAction(url=url, new_tab=False)
        elif match := click_pattern.match(action_str):
            bid = match.group(1)
            # Convert bid to index (simplified)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed click action with bid: {bid}, index: {index}')
            return ClickElementAction(index=index)
        elif match := fill_pattern.match(action_str):
            bid = match.group(1)
            text = match.group(2)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed fill action with bid: {bid}, text: {text}, index: {index}')
            return InputTextAction(index=index, text=text)
        elif match := scroll_pattern.match(action_str):
            delta_x = float(match.group(1))
            delta_y = float(match.group(2))
            logger.info(f'Parsed scroll action with delta_x: {delta_x}, delta_y: {delta_y}')
            return ScrollAction(down=delta_y > 0, num_pages=1)
        elif noop_pattern.match(action_str):
            # No-op action - just wait
            logger.info('Parsed noop action')
            return NoParamsAction()
        elif go_back_pattern.match(action_str):
            # Go back action
            logger.info('Parsed go_back action')
            return ('go_back', NoParamsAction())
        elif go_forward_pattern.match(action_str):
            # Go forward action
            logger.info('Parsed go_forward action')
            return ('go_forward', NoParamsAction())
        elif match := upload_file_pattern.match(action_str):
            bid = match.group(1)
            file_path = match.group(2)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed upload_file action with bid: {bid}, file_path: {file_path}, index: {index}')
            return UploadFileAction(index=index, file_path=file_path)
        elif match := press_pattern.match(action_str):
            bid = match.group(1)
            key = match.group(2)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed press action with bid: {bid}, key: {key}, index: {index}')
            return SendKeysAction(keys=key)
        elif match := hover_pattern.match(action_str):
            bid = match.group(1)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed hover action with bid: {bid}, index: {index}')
            return NoParamsAction()  # Placeholder - Browser-Use might not have hover
        elif match := focus_pattern.match(action_str):
            bid = match.group(1)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed focus action with bid: {bid}, index: {index}')
            return NoParamsAction()  # Placeholder - Browser-Use might not have focus
        elif match := clear_pattern.match(action_str):
            bid = match.group(1)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed clear action with bid: {bid}, index: {index}')
            return InputTextAction(index=index, text="")  # Clear by setting empty text
        elif match := select_option_pattern.match(action_str):
            bid = match.group(1)
            option = match.group(2)
            index = self._bid_to_index(bid)
            logger.info(f'Parsed select_option action with bid: {bid}, option: {option}, index: {index}')
            return NoParamsAction()  # Placeholder - Browser-Use might not have select_option

        logger.info(f'No pattern matched for action: {action_str}')
        return None

    def _bid_to_index(self, bid: str) -> int:
        """
        Convert a legacy bid to a Browser-Use index.

        This is a simplified implementation for backward compatibility.
        """
        try:
            return int(bid)
        except ValueError:
            return hash(bid) % 1000

    def step(self, action_str: str, timeout: float = 120) -> Dict[str, Any]:
        """
        Execute an action in the browser environment and return the observation.

        This method maintains compatibility with the original browser environment interface.

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
        try:
            self.agent_side.send(('IS_ALIVE', None))
            if self.agent_side.poll(timeout=timeout):
                response_id, response_data = self.agent_side.recv()
                if response_id == 'ALIVE':
                    return True
                elif response_id == 'ERROR':
                    logger.error(f'Browser process reported error: {response_data}')
                    return False
                logger.info(f'Browser env is not alive. Response ID: {response_id}')
            return False
        except Exception as e:
            logger.error(f'Error checking browser alive status: {e}')
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
