import argparse
import logging
import os
import pathlib
import platform

import toml
from dotenv import load_dotenv

from opendevin.schema import ConfigType

logger = logging.getLogger(__name__)

DEFAULT_CONTAINER_IMAGE = 'ghcr.io/opendevin/sandbox'
if os.getenv('OPEN_DEVIN_BUILD_VERSION'):
    DEFAULT_CONTAINER_IMAGE += ':' + (os.getenv('OPEN_DEVIN_BUILD_VERSION') or '')
else:
    DEFAULT_CONTAINER_IMAGE += ':main'

load_dotenv()

DEFAULT_CONFIG: dict = {
    'llm': {
        'api_key': None,
        'base_url': None,
        'model': 'gpt-3.5-turbo-1106',
        'embedding': {
            'model': 'local',
            'base_url': None,
            'deployment_name': None,
            'api_version': None,
        },
        'num_retries': 5,
        'retry_min_wait': 3,
        'retry_max_wait': 60,
        'timeout': None,
        'max_return_tokens': None,
        'max_chars': 5_000_000,
    },
    'agent': {
        'name': 'MonologueAgent',
        'memory': {
            'enabled': False,
            'max_threads': 2,
        },
    },
    'workspace_base': os.getcwd(),
    'workspace_mount_path': None,
    'workspace_mount_path_in_sandbox': '/workspace',
    'workspace_mount_rewrite': None,
    'cache_dir': '/tmp/cache',
    'sandbox_container_image': DEFAULT_CONTAINER_IMAGE,
    'run_as_devin': 'true',
    'max_iterations': 100,
    'e2b_api_key': '',
    'sandbox_type': 'ssh',
    'use_host_network': 'false',
    'ssh_hostname': 'localhost',
    'disable_color': 'false',
    'sandbox_user_id': os.getuid() if hasattr(os, 'getuid') else None,
    'sandbox_timeout': 120,
    'github_token': None,
    'sandbox_user_id': None
}

config_str = ''
if os.path.exists('config.toml'):
    with open('config.toml', 'rb') as f:
        config_str = f.read().decode('utf-8')


def int_value(value, default, config_key):
    # FIXME use a library
    try:
        return int(value)
    except ValueError:
        logger.warning(f'Invalid value for {config_key}: {value} not applied. Using default value {default}')
        return default


# Read config from environment variables and config.toml
def read_config(config, tomlConfig, env):
    for k, v in config.items():
        if isinstance(v, dict):
            read_config(v, tomlConfig.get(k, None), env.get(k, None))
        else:
            if k in env:
                config[k] = env[k]
            elif k in tomlConfig:
                config[k] = tomlConfig[k]
            if k in [ConfigType.LLM_NUM_RETRIES, ConfigType.LLM_RETRY_MIN_WAIT, ConfigType.LLM_RETRY_MAX_WAIT]:
                config[k] = int_value(config[k], v, config_key=k)

tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
read_config(config, tomlConfig, os.environ)

# TODO Compatibility
def compat_env_to_config(config, env):
    for k, v in env.items():
        if k.isupper():
            parts = k.lower().split('_')
            if len(parts) > 1 and parts[0] in config:
                sub_dict = config
                for part in parts[:-1]:
                    if part in sub_dict:
                        sub_dict = sub_dict[part]
                    else:
                        break
                else:
                    sub_dict[parts[-1]] = v

compat_env_to_config(config, os.environ)

# In local there is no sandbox, the workspace will have the same pwd as the host
if config[ConfigType.SANDBOX_TYPE] == 'local':
    config[ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX] = config[ConfigType.WORKSPACE_MOUNT_PATH]

def get_parser():
    parser = argparse.ArgumentParser(
        description='Run an agent with a specific task')
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    parser.add_argument(
        '-t', '--task', type=str, default='', help='The task for the agent to perform'
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Path to a file containing the task. Overrides -t if both are provided.',
    )
    parser.add_argument(
        '-c',
        '--agent-cls',
        default=config.get(ConfigType.AGENT),
        type=str,
        help='The agent class to use',
    )
    parser.add_argument(
        '-m',
        '--model-name',
        default=config.get(ConfigType.LLM_MODEL),
        type=str,
        help='The (litellm) model name to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=config.get(ConfigType.MAX_ITERATIONS),
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-n',
        '--max-chars',
        default=config.get(ConfigType.MAX_CHARS),
        type=int,
        help='The maximum number of characters to send to and receive from LLM per task',
    )
    return parser


def parse_arguments():
    parser = get_parser()
    args, _ = parser.parse_known_args()
    if args.directory:
        config[ConfigType.WORKSPACE_BASE] = os.path.abspath(args.directory)
        print(f'Setting workspace base to {config[ConfigType.WORKSPACE_BASE]}')
    return args


args = parse_arguments()


def finalize_config():
    if config.get(ConfigType.WORKSPACE_MOUNT_REWRITE) and not config.get(ConfigType.WORKSPACE_MOUNT_PATH):
        base = config.get(ConfigType.WORKSPACE_BASE) or os.getcwd()
        parts = config[ConfigType.WORKSPACE_MOUNT_REWRITE].split(':')
        config[ConfigType.WORKSPACE_MOUNT_PATH] = base.replace(parts[0], parts[1])

    if config.get(ConfigType.WORKSPACE_MOUNT_PATH) is None:
        config[ConfigType.WORKSPACE_MOUNT_PATH] = os.path.abspath(config[ConfigType.WORKSPACE_BASE])

    if config.get(ConfigType.LLM_EMBEDDING_BASE_URL) is None:
        config[ConfigType.LLM_EMBEDDING_BASE_URL] = config.get(ConfigType.LLM_BASE_URL)

    USE_HOST_NETWORK = config[ConfigType.USE_HOST_NETWORK].lower() != 'false'
    if USE_HOST_NETWORK and platform.system() == 'Darwin':
        logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )
    config[ConfigType.USE_HOST_NETWORK] = USE_HOST_NETWORK

    if config.get(ConfigType.WORKSPACE_MOUNT_PATH) is None:
        config[ConfigType.WORKSPACE_MOUNT_PATH] = config.get(ConfigType.WORKSPACE_BASE)


finalize_config()


def get(key: ConfigType, required: bool = False):
    """
    Get a key from the environment variables or config.toml or default configs.
    """
    if not isinstance(key, ConfigType):
        raise ValueError(f"key '{key}' must be an instance of ConfigType Enum")
    value = config.get(key)
    if not value and required:
        raise KeyError(f"Please set '{key}' in `config.toml` or `.env`.")
    return value


_cache_dir = config.get(ConfigType.CACHE_DIR)
if _cache_dir:
    pathlib.Path(_cache_dir).mkdir(parents=True, exist_ok=True)
