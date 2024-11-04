import argparse
import os
import pathlib
import platform
from dataclasses import is_dataclass
from functools import wraps
from types import UnionType
from typing import Any, Callable, MutableMapping, TypeVar, get_args, get_origin

import toml
from dotenv import load_dotenv

from openhands.core import logger
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.app_config import AppConfig
from openhands.core.config.config_utils import (
    OH_DEFAULT_AGENT,
    OH_MAX_ITERATIONS,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.sandbox_config import SandboxConfig

load_dotenv()

T = TypeVar('T')

def config_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for config operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except (ValueError, TypeError, KeyError) as e:
                logger.openhands_logger.warning(
                    f'Cannot parse config during {operation_name}, values have not been applied.\nError: {e}',
                    exc_info=False,
                )
            except FileNotFoundError as e:
                logger.openhands_logger.error(f'Config file not found: {e}')
            except toml.TomlDecodeError as e:
                logger.openhands_logger.warning(
                    f'Cannot parse config from toml during {operation_name}.\nError: {e}',
                    exc_info=False,
                )
            return None
        return wrapper
    return decorator

def get_optional_type(union_type: UnionType) -> Any:
    """Returns the non-None type from a Union."""
    types = get_args(union_type)
    return next((t for t in types if t is not type(None)), None)

def set_attr_from_env(sub_config: Any, env_or_toml_dict: dict, prefix=''):
    """Set attributes of a config dataclass based on environment variables."""
    for field_name, field_type in sub_config.__annotations__.items():
        env_var_name = (prefix + field_name).upper()

        if is_dataclass(field_type):
            nested_sub_config = getattr(sub_config, field_name)
            set_attr_from_env(nested_sub_config, env_or_toml_dict, prefix=field_name + '_')
        elif env_var_name in env_or_toml_dict:
            value = env_or_toml_dict[env_var_name]
            if not value:
                continue

            try:
                if get_origin(field_type) is UnionType:
                    field_type = get_optional_type(field_type)

                cast_value = (str(value).lower() in ['true', '1']) if field_type is bool else field_type(value)
                setattr(sub_config, field_name, cast_value)
            except (ValueError, TypeError):
                logger.openhands_logger.error(
                    f'Error setting env var {env_var_name}={value}: check that the value is of the right type'
                )

def load_from_env(cfg: AppConfig, env_or_toml_dict: dict | MutableMapping[str, str]):
    """Reads env-style vars and sets config attributes based on env vars or config.toml dict."""
    set_attr_from_env(cfg, env_or_toml_dict)
    default_llm_config = cfg.get_llm_config()
    set_attr_from_env(default_llm_config, env_or_toml_dict, 'LLM_')
    default_agent_config = cfg.get_agent_config()
    set_attr_from_env(default_agent_config, env_or_toml_dict, 'AGENT_')

@config_operation("toml_load")
def load_from_toml(cfg: AppConfig, toml_file: str = 'config.toml'):
    """Load the config from the toml file."""
    with open(toml_file, 'r', encoding='utf-8') as toml_contents:
        toml_config = toml.load(toml_contents)

    if 'core' not in toml_config:
        load_from_env(cfg, toml_config)
        return

    core_config = toml_config['core']

    for key, value in toml_config.items():
        if isinstance(value, dict):
            if key and key.lower() == 'agent':
                logger.openhands_logger.debug('Attempt to load default agent config from config toml')
                non_dict_fields = {k: v for k, v in value.items() if not isinstance(v, dict)}
                agent_config = AgentConfig(**non_dict_fields)
                cfg.set_agent_config(agent_config, 'agent')
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, dict):
                        logger.openhands_logger.debug(
                            f'Attempt to load group {nested_key} from config toml as agent config'
                        )
                        agent_config = AgentConfig(**nested_value)
                        cfg.set_agent_config(agent_config, nested_key)
            elif key and key.lower() == 'llm':
                logger.openhands_logger.debug('Attempt to load default LLM config from config toml')
                llm_config = LLMConfig.from_dict(value)
                cfg.set_llm_config(llm_config, 'llm')
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, dict):
                        logger.openhands_logger.debug(
                            f'Attempt to load group {nested_key} from config toml as llm config'
                        )
                        llm_config = LLMConfig.from_dict(nested_value)
                        cfg.set_llm_config(llm_config, nested_key)
            elif not key.startswith('sandbox') and key.lower() != 'core':
                logger.openhands_logger.warning(f'Unknown key in {toml_file}: "{key}"')
        else:
            logger.openhands_logger.warning(f'Unknown key in {toml_file}: "{key}"')

    # Set sandbox config
    sandbox_config = cfg.sandbox
    keys_to_migrate = [key for key in core_config if key.startswith('sandbox_')]
    for key in keys_to_migrate:
        new_key = key.replace('sandbox_', '')
        if new_key in sandbox_config.__annotations__:
            setattr(sandbox_config, new_key, core_config.pop(key))
        else:
            logger.openhands_logger.warning(f'Unknown sandbox config: {key}')

    if 'sandbox' in toml_config:
        sandbox_config = SandboxConfig(**toml_config['sandbox'])

    cfg.sandbox = sandbox_config
    for key, value in core_config.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        else:
            logger.openhands_logger.warning(f'Unknown core config key: {key}')

    return cfg

def finalize_config(cfg: AppConfig):
    """More tweaks to the config after it's been loaded."""
    if cfg.workspace_base is not None:
        cfg.workspace_base = os.path.abspath(cfg.workspace_base)
        if cfg.workspace_mount_path is None:
            cfg.workspace_mount_path = cfg.workspace_base

        if cfg.workspace_mount_rewrite:
            base = cfg.workspace_base or os.getcwd()
            parts = cfg.workspace_mount_rewrite.split(':')
            cfg.workspace_mount_path = base.replace(parts[0], parts[1])

    for llm in cfg.llms.values():
        llm.log_completions_folder = os.path.abspath(llm.log_completions_folder)
        if llm.embedding_base_url is None:
            llm.embedding_base_url = llm.base_url

    if cfg.sandbox.use_host_network and platform.system() == 'Darwin':
        logger.openhands_logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )

    if cfg.cache_dir:
        pathlib.Path(cfg.cache_dir).mkdir(parents=True, exist_ok=True)

@config_operation("llm_config_load")
def get_llm_config_arg(llm_config_arg: str, toml_file: str = 'config.toml') -> LLMConfig | None:
    """Get a group of llm settings from the config file."""
    llm_config_arg = llm_config_arg.strip('[]')
    if llm_config_arg.startswith('llm.'):
        llm_config_arg = llm_config_arg[4:]

    logger.openhands_logger.debug(f'Loading llm config from {llm_config_arg}')

    with open(toml_file, 'r', encoding='utf-8') as toml_contents:
        toml_config = toml.load(toml_contents)

    if 'llm' in toml_config and llm_config_arg in toml_config['llm']:
        return LLMConfig.from_dict(toml_config['llm'][llm_config_arg])
    
    logger.openhands_logger.debug(f'Loading from toml failed for {llm_config_arg}')
    return None

def get_parser() -> argparse.ArgumentParser:
    """Get the parser for the command line arguments."""
    parser = argparse.ArgumentParser(description='Run an agent with a specific task')
    parser.add_argument(
        '--config-file',
        type=str,
        default='config.toml',
        help='Path to the config file (default: config.toml in the current directory)',
    )
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    parser.add_argument(
        '-t',
        '--task',
        type=str,
        default='',
        help='The task for the agent to perform',
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
        default=OH_DEFAULT_AGENT,
        type=str,
        help='Name of the default agent to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=OH_MAX_ITERATIONS,
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-b',
        '--max-budget-per-task',
        type=float,
        help='The maximum budget allowed per task, beyond which the agent will stop.',
    )
    parser.add_argument(
        '--eval-output-dir',
        default='evaluation/evaluation_outputs/outputs',
        type=str,
        help='The directory to save evaluation output',
    )
    parser.add_argument(
        '--eval-n-limit',
        default=None,
        type=int,
        help='The number of instances to evaluate',
    )
    parser.add_argument(
        '--eval-num-workers',
        default=4,
        type=int,
        help='The number of workers to use for evaluation',
    )
    parser.add_argument(
        '--eval-note',
        default=None,
        type=str,
        help='The note to add to the evaluation directory',
    )
    parser.add_argument(
        '-l',
        '--llm-config',
        default=None,
        type=str,
        help='Replace default LLM ([llm] section in config.toml) config with the specified LLM config',
    )
    parser.add_argument(
        '-n',
        '--name',
        default='default',
        type=str,
        help='Name for the session',
    )
    parser.add_argument(
        '--eval-ids',
        default=None,
        type=str,
        help='The comma-separated list (in quotes) of IDs of the instances to evaluate',
    )
    return parser

def parse_arguments() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = get_parser()
    parsed_args, _ = parser.parse_known_args()
    return parsed_args

def load_app_config(
    set_logging_levels: bool = True, config_file: str = 'config.toml'
) -> AppConfig:
    """Load the configuration from the specified config file and environment variables."""
    config = AppConfig()
    load_from_toml(config, config_file)
    load_from_env(config, os.environ)
    finalize_config(config)
    if set_logging_levels:
        logger.DEBUG = config.debug
        logger.DISABLE_COLOR_PRINTING = config.disable_color
    return config

