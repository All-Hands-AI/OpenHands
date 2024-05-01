import atexit
import base64
import io
import time
import uuid
from multiprocessing import Pipe, Process

import browsergym.core  # noqa F401 (we register the openended task as a gym environment)
import gymnasium as gym
import numpy as np
from PIL import Image

from opendevin.logger import opendevin_logger as logger


class BrowserException(Exception):
    pass

class BrowserEnv:

    def __init__(self):
        # Initialize browser environment process
        self.browser_side, self.agent_side = Pipe()
        self.process = Process(target=self.browser_process,)
        logger.info('Starting browser env...')
        self.process.start()
        atexit.register(self.close)

    def browser_process(self):
        env = gym.make(
            'browsergym/openended',
            start_url='about:blank',
            wait_for_user_message=False,
            headless=True,
            disable_env_checker=True,
        )
        obs, info = env.reset()
        while True:
            try:
                if self.browser_side.poll(timeout=0.01):
                    unique_request_id , action_data = self.browser_side.recv()
                    # shutdown the browser environment
                    if unique_request_id == 'SHUTDOWN':
                        env.close()
                        return
                    action = action_data['action']
                    obs, reward, terminated, truncated, info = env.step(action)
                    # make observation serializable
                    obs['screenshot'] = self.image_to_png_base64_url(obs['screenshot'])
                    obs['active_page_index'] = obs['active_page_index'].item()
                    obs['elapsed_time'] = obs['elapsed_time'].item()
                    self.browser_side.send((unique_request_id, obs))
            except KeyboardInterrupt:
                logger.info('Browser env process interrupted by user.')
                return

    def step(self, action_str: str, timeout: float = 10) -> dict:
        unique_request_id = str(uuid.uuid4())
        self.agent_side.send((unique_request_id, {'action': action_str}))
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError('Browser environment took too long to respond.')
            if self.agent_side.poll(timeout=0.01):
                response_id, obs = self.agent_side.recv()
                if response_id == unique_request_id:
                    if obs['last_action_error']:
                        raise BrowserException(obs['last_action_error'])
                    return obs

    def close(self):
        logger.info('Shutting down browser env...')
        self.agent_side.send(('SHUTDOWN', None))
        self.process.join()

    @staticmethod
    def image_to_png_base64_url(image: np.ndarray | Image.Image):
        """Convert a numpy array to a base64 encoded png image url."""

        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        if image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        buffered = io.BytesIO()
        image.save(buffered, format='PNG')

        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f'{image_base64}'
