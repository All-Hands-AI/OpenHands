import argparse
import logging
import os
import pathlib
import platform

import toml
from dotenv import load_dotenv

from opendevin.core.schema import ConfigType

logger = logging.getLogger(__name__)

DEFAULT_CONTAINER_IMAGE = 'ghcr.io/opendevin/sandbox'
if os.getenv('OPEN_DEVIN_BUILD_VERSION'):
    DEFAULT_CONTAINER_IMAGE += ':' + (os.getenv('OPEN_DEVIN_BUILD_VERSION') or '')
else:
    DEFAULT_CONTAINER_IMAGE += ':main'

load_dotenv()

DEFAULT_CONFIG: dict = {
    ConfigType.LLM_API_KEY: None,
    ConfigType.LLM_BASE_URL: None,
    ConfigType.LLM_CUSTOM_LLM_PROVIDER: None,
    ConfigType.AWS_ACCESS_KEY_ID: None,
    ConfigType.AWS_SECRET_ACCESS_KEY: None,
    ConfigType.AWS_REGION_NAME: None,
    ConfigType.WORKSPACE_BASE: os.getcwd(),
    ConfigType.WORKSPACE_MOUNT_PATH: None,
    ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX: '/workspace',
    ConfigType.WORKSPACE_MOUNT_REWRITE: None,
    ConfigType.CACHE_DIR: '/tmp/cache',  # '/tmp/cache' is the default cache directory
    ConfigType.LLM_MODEL: 'gpt-3.5-turbo-1106',
    ConfigType.SANDBOX_CONTAINER_IMAGE: DEFAULT_CONTAINER_IMAGE,
    ConfigType.RUN_AS_DEVIN: 'true',
    ConfigType.LLM_EMBEDDING_MODEL: 'local',
    ConfigType.LLM_EMBEDDING_BASE_URL: None,
    ConfigType.LLM_EMBEDDING_DEPLOYMENT_NAME: None,
    ConfigType.LLM_API_VERSION: None,
    ConfigType.LLM_NUM_RETRIES: 5,
    ConfigType.LLM_RETRY_MIN_WAIT: 3,
    ConfigType.LLM_RETRY_MAX_WAIT: 60,
    ConfigType.MAX_ITERATIONS: 100,
    ConfigType.LLM_MAX_INPUT_TOKENS: None,
    ConfigType.LLM_MAX_OUTPUT_TOKENS: None,
    ConfigType.AGENT_MEMORY_MAX_THREADS: 2,
    ConfigType.AGENT_MEMORY_ENABLED: False,
    ConfigType.LLM_TIMEOUT: None,
    ConfigType.LLM_TEMPERATURE: None,
    ConfigType.LLM_TOP_P: None,
    # GPT-4 pricing is $10 per 1M input tokens. Since tokenization happens on LLM side,
    # we cannot easily count number of tokens, but we can count characters.
    # Assuming 5 characters per token, 5 million is a reasonable default limit.
    ConfigType.MAX_CHARS: 5_000_000,
    ConfigType.AGENT: 'CodeActAgent',
    ConfigType.E2B_API_KEY: '',
    ConfigType.SANDBOX_TYPE: 'ssh',  # Can be 'ssh', 'exec', or 'e2b'
    ConfigType.USE_HOST_NETWORK: 'false',
    ConfigType.SSH_HOSTNAME: 'localhost',
    ConfigType.DISABLE_COLOR: 'false',
    ConfigType.SANDBOX_USER_ID: os.getuid() if hasattr(os, 'getuid') else None,
    ConfigType.SANDBOX_TIMEOUT: 120,
    ConfigType.GITHUB_TOKEN: None,
    ConfigType.SANDBOX_USER_ID: None,
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
        logger.warning(
            f'Invalid value for {config_key}: {value} not applied. Using default value {default}'
        )
        return default


tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
for k, v in config.items():
    if k in os.environ:
        config[k] = os.environ[k]
    elif k in tomlConfig:
        config[k] = tomlConfig[k]
    if k in [
        ConfigType.LLM_NUM_RETRIES,
        ConfigType.LLM_RETRY_MIN_WAIT,
        ConfigType.LLM_RETRY_MAX_WAIT,
    ]:
        config[k] = int_value(config[k], v, config_key=k)

# In local there is no sandbox, the workspace will have the same pwd as the host
if config[ConfigType.SANDBOX_TYPE] == 'local':
    config[ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX] = config[
        ConfigType.WORKSPACE_MOUNT_PATH
    ]


def get_parser():
    parser = argparse.ArgumentParser(description='Run an agent with a specific task')
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
    if config.get(ConfigType.WORKSPACE_MOUNT_REWRITE) and not config.get(
        ConfigType.WORKSPACE_MOUNT_PATH
    ):
        base = config.get(ConfigType.WORKSPACE_BASE) or os.getcwd()
        parts = config[ConfigType.WORKSPACE_MOUNT_REWRITE].split(':')
        config[ConfigType.WORKSPACE_MOUNT_PATH] = base.replace(parts[0], parts[1])

    if config.get(ConfigType.WORKSPACE_MOUNT_PATH) is None:
        config[ConfigType.WORKSPACE_MOUNT_PATH] = os.path.abspath(
            config[ConfigType.WORKSPACE_BASE]
        )

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
