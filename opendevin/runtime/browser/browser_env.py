import atexit
import base64
import io
import json
import multiprocessing
import os
import threading
import time
import uuid

import browsergym.core  # noqa F401 (we register the openended task as a gym environment)
import gymnasium as gym
import html2text
import numpy as np
from browsergym.utils.obs import flatten_dom_to_str
from PIL import Image

from opendevin.core.exceptions import BrowserInitException
from opendevin.core.logger import opendevin_logger as logger


class BrowserEnv:
    def __init__(
        self,
        is_async: bool = True,
        browsergym_eval: str = '',
        browsergym_eval_save_dir: str = '',
    ):
        self.html_text_converter = self.get_html_text_converter()
        self.eval_mode = False
        self.eval_dir = ''
        # EVAL only: browsergym_eval and browsergym_eval_save_dir must be provided for evaluation
        self.browsergym_eval = browsergym_eval
        self.browsergym_eval_save_dir = browsergym_eval_save_dir
        if self.browsergym_eval:
            assert (
                self.browsergym_eval_save_dir
            ), 'browsergym_eval_save_dir must be provided for evaluation.'
            self.eval_mode = True
            self.eval_dir = os.path.join(
                self.browsergym_eval_save_dir, self.browsergym_eval.split('/')[1]
            )
            os.makedirs(self.eval_dir, exist_ok=True)
        # Initialize browser environment process
        multiprocessing.set_start_method('spawn', force=True)
        self.browser_side, self.agent_side = multiprocessing.Pipe()
        self.process = multiprocessing.Process(
            target=self.browser_process,
        )

        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            logger.warning(
                'Current working directory does not exist. Using /tmp as fallback.'
            )
            self.original_cwd = '/tmp'
            os.chdir('/tmp')

        if is_async:
            threading.Thread(target=self.init_browser).start()
        else:
            self.init_browser()
        atexit.register(self.close)

    def get_html_text_converter(self):
        html_text_converter = html2text.HTML2Text()
        # ignore links and images
        html_text_converter.ignore_links = False
        html_text_converter.ignore_images = True
        # use alt text for images
        html_text_converter.images_to_alt = True
        # disable auto text wrapping
        html_text_converter.body_width = 0
        return html_text_converter

    def init_browser(self):
        logger.info('Starting browser env...')

        # Ensure we're in a valid directory before starting the process
        try:
            os.chdir(self.original_cwd)
            logger.debug(f'Changed back to original directory: {self.original_cwd}')
        except Exception as e:
            logger.error(f'Failed to change to original directory: {e}')
            # If we can't change to the original directory, try to use a known valid directory
            os.chdir('/tmp')
            logger.debug('Changed to /tmp directory as fallback')

        try:
            self.process.start()
        except Exception as e:
            logger.error(f'Failed to start browser process: {e}')
            raise

        if not self.check_alive():
            self.close()
            raise BrowserInitException('Failed to start browser environment.')

    def browser_process(self):
        if self.eval_mode:
            logger.info('Creating browser env for evaluation purpose.')
            env = gym.make(self.browsergym_eval)
        else:
            env = gym.make(
                'browsergym/openended',
                task_kwargs={'start_url': 'about:blank', 'goal': 'PLACEHOLDER_GOAL'},
                wait_for_user_message=False,
                headless=True,
                disable_env_checker=True,
            )
        obs, info = env.reset()
        # EVAL only: save the goal into file for evaluation
        if self.eval_mode:
            rewards = []  # store rewards if in eval mode
            logger.info(obs['goal'])
            with open(
                os.path.join(self.eval_dir, 'goal.txt'), 'w', encoding='utf-8'
            ) as f:
                f.write(obs['goal'])
        logger.info('Browser env started.')
        while True:
            try:
                if self.browser_side.poll(timeout=0.01):
                    unique_request_id, action_data = self.browser_side.recv()
                    # shutdown the browser environment
                    if unique_request_id == 'SHUTDOWN':
                        logger.info('SHUTDOWN recv, shutting down browser env...')
                        env.close()
                        return
                    elif unique_request_id == 'IS_ALIVE':
                        self.browser_side.send(('ALIVE', None))
                        continue
                    action = action_data['action']
                    obs, reward, terminated, truncated, info = env.step(action)
                    # EVAL only: save the rewards into file for evaluation
                    if self.eval_mode:
                        rewards.append(reward)
                        with open(
                            os.path.join(self.eval_dir, 'rewards.json'),
                            'w',
                            encoding='utf-8',
                        ) as f:
                            f.write(json.dumps(rewards))
                    # add text content of the page
                    html_str = flatten_dom_to_str(obs['dom_object'])
                    obs['text_content'] = self.html_text_converter.handle(html_str)
                    # make observation serializable
                    obs['screenshot'] = self.image_to_png_base64_url(obs['screenshot'])
                    obs['active_page_index'] = obs['active_page_index'].item()
                    obs['elapsed_time'] = obs['elapsed_time'].item()
                    self.browser_side.send((unique_request_id, obs))
            except KeyboardInterrupt:
                logger.info('Browser env process interrupted by user.')
                try:
                    env.close()
                except Exception:
                    pass
                return

    def step(self, action_str: str, timeout: float = 30) -> dict:
        unique_request_id = str(uuid.uuid4())
        self.agent_side.send((unique_request_id, {'action': action_str}))
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError('Browser environment took too long to respond.')
            if self.agent_side.poll(timeout=0.01):
                response_id, obs = self.agent_side.recv()
                if response_id == unique_request_id:
                    return obs

    def check_alive(self, timeout: float = 60):
        self.agent_side.send(('IS_ALIVE', None))
        if self.agent_side.poll(timeout=timeout):
            response_id, _ = self.agent_side.recv()
            if response_id == 'ALIVE':
                return True
            logger.info(f'Browser env is not alive. Response ID: {response_id}')

    def close(self):
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
        except Exception:
            logger.error('Encountered an error when closing browser env', exc_info=True)

    @staticmethod
    def image_to_png_base64_url(
        image: np.ndarray | Image.Image, add_data_prefix: bool = False
    ):
        """Convert a numpy array to a base64 encoded png image url."""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        if image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        buffered = io.BytesIO()
        image.save(buffered, format='PNG')

        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        return (
            f'data:image/png;base64,{image_base64}'
            if add_data_prefix
            else f'{image_base64}'
        )

    @staticmethod
    def image_to_jpg_base64_url(
        image: np.ndarray | Image.Image, add_data_prefix: bool = False
    ):
        """Convert a numpy array to a base64 encoded jpeg image url."""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        if image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        buffered = io.BytesIO()
        image.save(buffered, format='JPEG')

        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        return (
            f'data:image/jpeg;base64,{image_base64}'
            if add_data_prefix
            else f'{image_base64}'
        )
