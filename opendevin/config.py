import copy
import os

import toml
from dotenv import load_dotenv

from opendevin.schema import ConfigType

load_dotenv()

DEFAULT_CONFIG: dict = {
    ConfigType.LLM_API_KEY: None,
    ConfigType.LLM_BASE_URL: None,
    ConfigType.WORKSPACE_DIR: os.path.join(os.getcwd(), 'workspace'),
    ConfigType.LLM_MODEL: 'gpt-3.5-turbo-1106',
    ConfigType.SANDBOX_CONTAINER_IMAGE: 'ghcr.io/opendevin/sandbox',
    ConfigType.RUN_AS_DEVIN: 'true',
    ConfigType.LLM_EMBEDDING_MODEL: 'local',
    ConfigType.LLM_DEPLOYMENT_NAME: None,
    ConfigType.LLM_API_VERSION: None,
    ConfigType.LLM_NUM_RETRIES: 6,
    ConfigType.LLM_COOLDOWN_TIME: 1,
    ConfigType.DIRECTORY_REWRITE: '',
    ConfigType.MAX_ITERATIONS: 100,
    ConfigType.AGENT: 'MonologueAgent',
    ConfigType.SANDBOX_TYPE: 'ssh'
}

config_str = ''
if os.path.exists('config.toml'):
    with open('config.toml', 'rb') as f:
        config_str = f.read().decode('utf-8')

tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
for k, v in config.items():
    if k in os.environ:
        config[k] = os.environ[k]
    elif k in tomlConfig:
        config[k] = tomlConfig[k]


def get(key: str, default=None, required=False):
    """
    Get a key from the environment variables or config.toml or default configs.
    """
    value = config.get(key, default)
    if not value and required:
        raise KeyError(f"Please set '{key}' in `config.toml` or `.env`.")
    return value


def get_fe_config() -> dict:
    """
    Get all the frontend configuration values by performing a deep copy.
    """
    fe_config = copy.deepcopy(config)
    del fe_config['LLM_API_KEY']
    return fe_config
