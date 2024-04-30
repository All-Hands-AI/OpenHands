import gymnasium as gym
import browsergym.core  # noqa F401 (we register the openended task as a gym environment)

from multiprocessing.connection import Connection

from opendevin.browser_server.utils import image_to_png_base64_url

def start_browser(conn: Connection):
    env = gym.make(
        'browsergym/openended',
        start_url='about:blank',
        wait_for_user_message=False,
        headless=True,
        disable_env_checker=True,
    )
    obs, info = env.reset()
    while True:
        if conn.poll():
            unique_request_id , action_data = conn.recv()
            action = action_data['action']
            obs, reward, terminated, truncated, info = env.step(action)
            # make observation serializable
            obs['screenshot'] = image_to_png_base64_url(obs['screenshot'])
            obs['active_page_index'] = int(obs['active_page_index'])
            obs['elapsed_time'] = float(obs['elapsed_time'])
            conn.send((unique_request_id, obs))
