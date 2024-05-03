import argparse
import logging
import os
import pathlib
import platform
from dataclasses import dataclass, field
from types import UnionType
from typing import get_args, get_origin

import toml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_CONTAINER_IMAGE = 'ghcr.io/opendevin/sandbox'
if os.getenv('OPEN_DEVIN_BUILD_VERSION'):
    DEFAULT_CONTAINER_IMAGE += ':' + (os.getenv('OPEN_DEVIN_BUILD_VERSION') or '')
else:
    DEFAULT_CONTAINER_IMAGE += ':main'

load_dotenv()


@dataclass
class LLMConfig:
    api_key: str | None = None
    base_url: str | None = None
    model: str = 'gpt-3.5-turbo-1106'
    api_version: str | None = None
    embedding_model: str = 'local'
    embedding_base_url: str | None = None
    embedding_deployment_name: str | None = None
    num_retries: int = 5
    retry_min_wait: int = 3
    retry_max_wait: int = 60
    timeout: int | None = None
    max_return_tokens: int | None = None
    max_chars: int = 5_000_000


@dataclass
class AgentConfig:
    name: str = 'MonologueAgent'
    memory_enabled: bool = False
    memory_max_threads: int = 2


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    workspace_base: str = os.getcwd()
    workspace_mount_path: str = os.path.abspath(workspace_base) # TODO this might not work, set at the end
    workspace_mount_path_in_sandbox: str = '/workspace'
    workspace_mount_rewrite: str | None = None
    cache_dir: str = '/tmp/cache'
    sandbox_container_image: str = DEFAULT_CONTAINER_IMAGE
    run_as_devin: bool = True
    max_iterations: int = 100
    e2b_api_key: str = ''
    sandbox_type: str = 'ssh'
    use_host_network: bool = False
    ssh_hostname: str = 'localhost'
    disable_color: bool = False
    sandbox_user_id: int = os.getuid() if hasattr(os, 'getuid') else 1000
    sandbox_timeout: int = 120
    github_token: str | None = None


# FIXME Compatibility
def compat_env_to_config(config, env_or_toml_dict):

    def get_optional_type(union_type):
        """Returns the non-None type from an Union."""
        types = get_args(union_type)
        return next((t for t in types if t is not type(None)), None)

    # helper function to set attributes based on env vars
    def set_attr_from_env(sub_config, prefix=''):
        """Set attributes of a config dataclass based on environment variables."""
        for field_name, field_type in sub_config.__annotations__.items():
            # compute the expected environment variable name from the prefix and field name
            env_var_name = (prefix + field_name).upper()

            if hasattr(field_type, '__annotations__'):  # Check if this is a nested data class
                # nested dataclass
                nested_sub_config = getattr(sub_config, field_name)
                set_attr_from_env(nested_sub_config, prefix=field_name + '_')
            elif env_var_name in env_or_toml_dict:
                # convert the env var to the correct type and set it
                value = env_or_toml_dict[env_var_name]
                try:
                    # if it's an optional type, get the non-None type
                    if get_origin(field_type) is UnionType:
                        field_type = get_optional_type(field_type)

                    # Attempt to cast the environment variable to the designated type
                    cast_value = field_type(value)
                    setattr(sub_config, field_name, cast_value)
                except (ValueError, TypeError):
                    # Log an error if casting fails
                    logger.error(f'Error setting env var {env_var_name}={value}: check that the value is of the right type')

    # Start processing from the root of the config object
    set_attr_from_env(config)

# FIXME make it a singleton
config = AppConfig()

# read the toml file
config_str = ''
if os.path.exists('config.toml'):
    with open('config.toml', 'rb') as f:
        config_str = f.read().decode('utf-8')

# load the toml config as a dict
tomlConfig = toml.loads(config_str)

try:
    # let's see if new-style toml is used
    llm_config = LLMConfig(**tomlConfig['llm'])
    agent_config = AgentConfig(**tomlConfig['agent'])
    config = AppConfig(
        llm=llm_config,
        agent=agent_config,
        **{k: v for k, v in tomlConfig.items() if k not in ['llm', 'agent']}
    )
except (TypeError, KeyError):
    # if not, we'll use the old-style toml
    compat_env_to_config(config, tomlConfig)

# read the config from env
compat_env_to_config(config, os.environ)


# In local there is no sandbox, the workspace will have the same pwd as the host
if config.sandbox_type == 'local':
    # TODO why do we seem to need None for these paths?
    config.workspace_mount_path_in_sandbox = config.workspace_mount_path


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
        default=config.agent.name,
        type=str,
        help='The agent class to use',
    )
    parser.add_argument(
        '-m',
        '--model-name',
        default=config.llm.model,
        type=str,
        help='The (litellm) model name to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=config.max_iterations,
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-n',
        '--max-chars',
        default=config.llm.max_chars,
        type=int,
        help='The maximum number of characters to send to and receive from LLM per task',
    )
    return parser


def parse_arguments():
    parser = get_parser()
    args, _ = parser.parse_known_args()
    if args.directory:
        config.workspace_base = os.path.abspath(args.directory)
        print(f'Setting workspace base to {config.workspace_base}')
    return args


args = parse_arguments()


def finalize_config():
    if config.workspace_mount_rewrite: # and not config.workspace_mount_path:
        # TODO why do we need to check if workspace_mount_path is None?
        base = config.workspace_base or os.getcwd()
        parts = config.workspace_mount_rewrite.split(':')
        config.workspace_mount_path = base.replace(parts[0], parts[1])

    if config.llm.embedding_base_url is None:
        config.llm.embedding_base_url = config.llm.base_url

    USE_HOST_NETWORK = config.use_host_network
    if USE_HOST_NETWORK and platform.system() == 'Darwin':
        logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )
    config.use_host_network = USE_HOST_NETWORK

    # TODO why was the last workspace_mount_path line unreachable?

finalize_config()


_cache_dir = config.cache_dir
if _cache_dir:
    pathlib.Path(_cache_dir).mkdir(parents=True, exist_ok=True)