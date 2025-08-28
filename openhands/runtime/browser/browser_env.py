import atexit
import multiprocessing
import os
import time
import uuid

import browsergym.core  # noqa F401 (we register the openended task as a gym environment)
import gymnasium as gym
import html2text
import tenacity
from browsergym.utils.obs import flatten_dom_to_str, overlay_som

from openhands.core.exceptions import BrowserInitException
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.browser.base64 import image_to_png_base64_url
from openhands.utils.shutdown_listener import should_continue, should_exit
from openhands.utils.tenacity_stop import stop_if_should_exit

BROWSER_EVAL_GET_GOAL_ACTION = 'GET_EVAL_GOAL'
BROWSER_EVAL_GET_REWARDS_ACTION = 'GET_EVAL_REWARDS'


class BrowserEnv:
    def __init__(self, browsergym_eval_env: str | None = None, browser_logging_dir: str | None = None):
        self.html_text_converter = self.get_html_text_converter()
        self.eval_mode = False
        self.eval_dir = ''
        
        # Browser state logging configuration (for WebArena evaluation)
        self.browser_logging_dir = browser_logging_dir
        self.enable_state_logging = browser_logging_dir is not None

        # Initialize browser environment process
        multiprocessing.set_start_method('spawn', force=True)
        self.browser_side, self.agent_side = multiprocessing.Pipe()

        self.init_browser()
        atexit.register(self.close)

    def get_html_text_converter(self) -> html2text.HTML2Text:
        html_text_converter = html2text.HTML2Text()
        # ignore links and images
        html_text_converter.ignore_links = False
        html_text_converter.ignore_images = True
        # use alt text for images
        html_text_converter.images_to_alt = True
        # disable auto text wrapping
        html_text_converter.body_width = 0
        return html_text_converter

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(5) | stop_if_should_exit(),
        retry=tenacity.retry_if_exception_type(BrowserInitException),
    )
    def init_browser(self) -> None:
        logger.debug('Starting browser env...')
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
        env = gym.make(
            'browsergym/openended',
            task_kwargs={'start_url': 'about:blank', 'goal': 'PLACEHOLDER_GOAL'},
            wait_for_user_message=False,
            headless=True,
            disable_env_checker=True,
            tags_to_mark='all',
            timeout=100000,
            pw_context_kwargs={'accept_downloads': True},
            pw_chromium_kwargs={'downloads_path': '/workspace/.downloads/'},
        )
        obs, info = env.reset()

        logger.info('Successfully called env.reset')
        logger.info('Browser env started.')
        
        # Initialize browser state capture for WebArena evaluation
        state_capture = None
        if self.enable_state_logging:
            try:
                from evaluation.benchmarks.webarena.browsergym_state_capture import BrowserGymStateCapture
                state_capture = BrowserGymStateCapture(output_dir=self.browser_logging_dir)
                logger.info(f'Browser state logging enabled: {self.browser_logging_dir}')
            except ImportError:
                logger.warning('Could not import BrowserGymStateCapture, state logging disabled')
                state_capture = None

        while should_continue():
            try:
                if self.browser_side.poll(timeout=0.01):
                    unique_request_id, action_data = self.browser_side.recv()

                    # shutdown the browser environment
                    if unique_request_id == 'SHUTDOWN':
                        logger.debug('SHUTDOWN recv, shutting down browser env...')
                        env.close()
                        return
                    elif unique_request_id == 'IS_ALIVE':
                        self.browser_side.send(('ALIVE', None))
                        continue
                    elif unique_request_id == 'SET_WEBARENA_INSTANCE':
                        # Set WebArena instance ID for state capture
                        if state_capture and 'instance_id' in action_data:
                            state_capture.set_instance_id(action_data['instance_id'])
                            logger.info(f'Set WebArena instance ID: {action_data["instance_id"]}')
                        self.browser_side.send((unique_request_id, {'status': 'ok'}))
                        continue
                    elif unique_request_id == 'CAPTURE_WEBARENA_STATE':
                        # Capture final browser state for WebArena evaluation
                        if state_capture:
                            try:
                                state_file = state_capture.save_state(env)
                                self.browser_side.send((unique_request_id, {'status': 'ok', 'state_file': state_file}))
                            except Exception as e:
                                logger.error(f'Failed to capture WebArena state: {e}')
                                self.browser_side.send((unique_request_id, {'status': 'error', 'error': str(e)}))
                        else:
                            self.browser_side.send((unique_request_id, {'status': 'disabled'}))
                        continue

                    action = action_data['action']
                    obs, reward, terminated, truncated, info = env.step(action)

                    # add text content of the page
                    html_str = flatten_dom_to_str(obs['dom_object'])
                    obs['text_content'] = self.html_text_converter.handle(html_str)
                    # make observation serializable
                    obs['set_of_marks'] = image_to_png_base64_url(
                        overlay_som(
                            obs['screenshot'], obs.get('extra_element_properties', {})
                        ),
                        add_data_prefix=True,
                    )
                    obs['screenshot'] = image_to_png_base64_url(
                        obs['screenshot'], add_data_prefix=True
                    )
                    obs['active_page_index'] = obs['active_page_index'].item()
                    obs['elapsed_time'] = obs['elapsed_time'].item()
                    self.browser_side.send((unique_request_id, obs))
            except KeyboardInterrupt:
                logger.debug('Browser env process interrupted by user.')
                try:
                    env.close()
                except Exception:
                    pass
                return

    def step(self, action_str: str, timeout: float = 120) -> dict:
        """Execute an action in the browser environment and return the observation."""
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
        self.agent_side.send(('IS_ALIVE', None))
        if self.agent_side.poll(timeout=timeout):
            response_id, _ = self.agent_side.recv()
            if response_id == 'ALIVE':
                return True
            logger.debug(f'Browser env is not alive. Response ID: {response_id}')
        return False
    
    def set_webarena_instance_id(self, instance_id: str, timeout: float = 10) -> bool:
        """Set the WebArena instance ID for browser state capture."""
        if not self.enable_state_logging:
            logger.warning('Browser state logging is not enabled')
            return False
        
        unique_request_id = 'SET_WEBARENA_INSTANCE'
        self.agent_side.send((unique_request_id, {'instance_id': instance_id}))
        start_time = time.time()
        while True:
            if should_exit() or time.time() - start_time > timeout:
                logger.error('Timeout setting WebArena instance ID')
                return False
            if self.agent_side.poll(timeout=0.01):
                response_id, response = self.agent_side.recv()
                if response_id == unique_request_id:
                    return response.get('status') == 'ok'
    
    def capture_webarena_state(self, timeout: float = 30) -> str | None:
        """Capture the current browser state for WebArena evaluation."""
        if not self.enable_state_logging:
            logger.warning('Browser state logging is not enabled')
            return None
        
        unique_request_id = 'CAPTURE_WEBARENA_STATE'
        self.agent_side.send((unique_request_id, {}))
        start_time = time.time()
        while True:
            if should_exit() or time.time() - start_time > timeout:
                logger.error('Timeout capturing WebArena state')
                return None
            if self.agent_side.poll(timeout=0.01):
                response_id, response = self.agent_side.recv()
                if response_id == unique_request_id:
                    if response.get('status') == 'ok':
                        return response.get('state_file')
                    else:
                        logger.error(f'Failed to capture state: {response.get("error", "unknown error")}')
                        return None

    def close(self) -> None:
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
