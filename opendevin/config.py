import copy
import os

import argparse
import toml
from dotenv import load_dotenv

from opendevin.schema import ConfigType

load_dotenv()

DEFAULT_CONFIG: dict = {
    ConfigType.LLM_API_KEY: None,
    ConfigType.LLM_BASE_URL: None,
    ConfigType.WORKSPACE_BASE: os.getcwd(),
    ConfigType.WORKSPACE_MOUNT_PATH: None,
    ConfigType.WORKSPACE_MOUNT_REWRITE: None,
    ConfigType.LLM_MODEL: 'gpt-3.5-turbo-1106',
    ConfigType.SANDBOX_CONTAINER_IMAGE: 'ghcr.io/opendevin/sandbox',
    ConfigType.RUN_AS_DEVIN: 'true',
    ConfigType.LLM_EMBEDDING_MODEL: 'local',
    ConfigType.LLM_DEPLOYMENT_NAME: None,
    ConfigType.LLM_API_VERSION: None,
    ConfigType.LLM_NUM_RETRIES: 5,
    ConfigType.LLM_COOLDOWN_TIME: 1,
    ConfigType.MAX_ITERATIONS: 100,
    # GPT-4 pricing is $10 per 1M input tokens. Since tokenization happens on LLM side,
    # we cannot easily count number of tokens, but we can count characters.
    # Assuming 5 characters per token, 5 million is a reasonable default limit.
    ConfigType.MAX_CHARS: 5_000_000,
    ConfigType.AGENT: 'MonologueAgent',
    ConfigType.SANDBOX_TYPE: 'ssh',
    ConfigType.USE_HOST_NETWORK: 'false',
    ConfigType.SSH_HOSTNAME: 'localhost',
    ConfigType.DISABLE_COLOR: 'false',
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Run an agent with a specific task')
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    args, _ = parser.parse_known_args()
    if args.directory:
        config[ConfigType.WORKSPACE_BASE] = os.path.abspath(args.directory)
        print(f"Setting workspace base to {config[ConfigType.WORKSPACE_BASE]}")


parse_arguments()


def finalize_config():
    if config.get(ConfigType.WORKSPACE_MOUNT_REWRITE) and not config.get(ConfigType.WORKSPACE_MOUNT_PATH):
        base = config.get(ConfigType.WORKSPACE_BASE) or os.getcwd()
        parts = config[ConfigType.WORKSPACE_MOUNT_REWRITE].split(':')
        config[ConfigType.WORKSPACE_MOUNT_PATH] = base.replace(parts[0], parts[1])


finalize_config()


def get(key: str, required: bool = False):
    """
    Get a key from the environment variables or config.toml or default configs.
    """
    value = config.get(key)
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
