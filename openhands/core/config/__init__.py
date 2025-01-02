import argparse

from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.app_config import AppConfig
from openhands.core.config.config_utils import (
    OH_DEFAULT_AGENT,
    OH_MAX_ITERATIONS,
    get_field_info,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig
from openhands.core.config.utils import (
    finalize_config,
    get_llm_config_arg,
    get_parser,
    load_app_config,
    load_from_env,
    load_from_toml,
    parse_arguments,
)

__all__ = [
    'OH_DEFAULT_AGENT',
    'OH_MAX_ITERATIONS',
    'AgentConfig',
    'AppConfig',
    'LLMConfig',
    'SandboxConfig',
    'SecurityConfig',
    'load_app_config',
    'load_from_env',
    'load_from_toml',
    'finalize_config',
    'get_llm_config_arg',
    'get_field_info',
    'get_parser',
    'parse_arguments',
]


def setup_config_from_args(args: argparse.Namespace) -> AppConfig:
    """Load config from toml and override with command line arguments.

    Common setup used by both CLI and main.py entry points.
    """
    # Load base config from toml and env vars
    config = load_app_config(config_file=args.config_file)

    # Override with command line arguments if provided
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')
        config.set_llm_config(llm_config)

    # Override default agent if provided
    if args.agent_cls:
        config.default_agent = args.agent_cls

    # Set max iterations and max budget per task if provided, otherwise fall back to config values
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations
    if args.max_budget_per_task is not None:
        config.max_budget_per_task = args.max_budget_per_task

    return config
