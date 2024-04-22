import os

import argparse
import toml
from dotenv import load_dotenv

from opendevin.schema import ConfigType
import logging

logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_CONFIG: dict = {
    ConfigType.LLM_API_KEY: None,
    ConfigType.LLM_BASE_URL: None,
    ConfigType.WORKSPACE_BASE: os.getcwd(),
    ConfigType.WORKSPACE_MOUNT_PATH: None,
    ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX: '/workspace',
    ConfigType.WORKSPACE_MOUNT_REWRITE: None,
    ConfigType.LLM_MODEL: 'gpt-3.5-turbo-1106',
    ConfigType.SANDBOX_CONTAINER_IMAGE: 'ghcr.io/opendevin/sandbox',
    ConfigType.RUN_AS_DEVIN: 'true',
    ConfigType.LLM_EMBEDDING_MODEL: 'local',
    ConfigType.LLM_EMBEDDING_DEPLOYMENT_NAME: None,
    ConfigType.LLM_API_VERSION: None,
    ConfigType.LLM_NUM_RETRIES: 5,
    ConfigType.LLM_RETRY_MIN_WAIT: 3,
    ConfigType.LLM_RETRY_MAX_WAIT: 60,
    ConfigType.MAX_ITERATIONS: 100,
    # GPT-4 pricing is $10 per 1M input tokens. Since tokenization happens on LLM side,
    # we cannot easily count number of tokens, but we can count characters.
    # Assuming 5 characters per token, 5 million is a reasonable default limit.
    ConfigType.MAX_CHARS: 5_000_000,
    ConfigType.AGENT: 'MonologueAgent',
    ConfigType.E2B_API_KEY: '',
    ConfigType.SANDBOX_TYPE: 'ssh',  # Can be 'ssh', 'exec', or 'e2b'
    ConfigType.USE_HOST_NETWORK: 'false',
    ConfigType.SSH_HOSTNAME: 'localhost',
    ConfigType.DISABLE_COLOR: 'false',
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


tomlConfig = toml.loads(config_str)
config = DEFAULT_CONFIG.copy()
for k, v in config.items():
    if k in os.environ:
        config[k] = os.environ[k]
    elif k in tomlConfig:
        config[k] = tomlConfig[k]
    if k in [ConfigType.LLM_NUM_RETRIES, ConfigType.LLM_RETRY_MIN_WAIT, ConfigType.LLM_RETRY_MAX_WAIT]:
        config[k] = int_value(config[k], v, config_key=k)


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
        default='MonologueAgent',
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


finalize_config()


def get(key: str, required: bool = False):
    """
    Get a key from the environment variables or config.toml or default configs.
    """
    value = config.get(key)
    if not value and required:
        raise KeyError(f"Please set '{key}' in `config.toml` or `.env`.")
    return value
