import argparse
import os
import pathlib
import platform
import sys
from ast import literal_eval
from types import UnionType
from typing import MutableMapping, get_args, get_origin
from uuid import uuid4

import toml
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr, ValidationError

from openhands import __version__
from openhands.core import logger
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.condenser_config import (
    CondenserConfig,
    condenser_config_from_toml_section,
    create_condenser_config,
)
from openhands.core.config.config_utils import (
    OH_DEFAULT_AGENT,
    OH_MAX_ITERATIONS,
)
from openhands.core.config.extended_config import ExtendedConfig
from openhands.core.config.kubernetes_config import KubernetesConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig
from openhands.storage import get_file_store
from openhands.storage.files import FileStore
from openhands.utils.import_utils import get_impl

JWT_SECRET = '.jwt_secret'
load_dotenv()


def load_from_env(
    cfg: OpenHandsConfig, env_or_toml_dict: dict | MutableMapping[str, str]
) -> None:
    """Sets config attributes from environment variables or TOML dictionary.

    Reads environment-style variables and updates the config attributes accordingly.
    Supports configuration of LLM settings (e.g., LLM_BASE_URL), agent settings
    (e.g., AGENT_MEMORY_ENABLED), sandbox settings (e.g., SANDBOX_TIMEOUT), and more.

    Args:
        cfg: The OpenHandsConfig object to set attributes on.
        env_or_toml_dict: The environment variables or a config.toml dict.
    """

    def get_optional_type(union_type: UnionType | type | None) -> type | None:
        """Returns the non-None type from a Union."""
        if union_type is None:
            return None
        if get_origin(union_type) is UnionType:
            types = get_args(union_type)
            return next((t for t in types if t is not type(None)), None)
        if isinstance(union_type, type):
            return union_type
        return None

    # helper function to set attributes based on env vars
    def set_attr_from_env(sub_config: BaseModel, prefix: str = '') -> None:
        """Set attributes of a config model based on environment variables."""
        for field_name, field_info in sub_config.__class__.model_fields.items():
            field_value = getattr(sub_config, field_name)
            field_type = field_info.annotation

            # compute the expected env var name from the prefix and field name
            # e.g. LLM_BASE_URL
            env_var_name = (prefix + field_name).upper()

            if isinstance(field_value, BaseModel):
                set_attr_from_env(field_value, prefix=field_name + '_')

            elif env_var_name in env_or_toml_dict:
                # convert the env var to the correct type and set it
                value = env_or_toml_dict[env_var_name]

                # skip empty config values (fall back to default)
                if not value:
                    continue

                try:
                    # if it's an optional type, get the non-None type
                    if get_origin(field_type) is UnionType:
                        field_type = get_optional_type(field_type)

                    # Attempt to cast the env var to type hinted in the dataclass
                    if field_type is bool:
                        cast_value = str(value).lower() in ['true', '1']
                    # parse dicts and lists like SANDBOX_RUNTIME_STARTUP_ENV_VARS and SANDBOX_RUNTIME_EXTRA_BUILD_ARGS                                                                                                                                     │
                    elif (
                        get_origin(field_type) is dict
                        or get_origin(field_type) is list
                        or field_type is dict
                        or field_type is list
                    ):
                        cast_value = literal_eval(value)
                    else:
                        if field_type is not None:
                            cast_value = field_type(value)
                    setattr(sub_config, field_name, cast_value)
                except (ValueError, TypeError):
                    logger.openhands_logger.error(
                        f'Error setting env var {env_var_name}={value}: check that the value is of the right type'
                    )

    # Start processing from the root of the config object
    set_attr_from_env(cfg)

    # load default LLM config from env
    default_llm_config = cfg.get_llm_config()
    set_attr_from_env(default_llm_config, 'LLM_')
    # load default agent config from env
    default_agent_config = cfg.get_agent_config()
    set_attr_from_env(default_agent_config, 'AGENT_')


def load_from_toml(cfg: OpenHandsConfig, toml_file: str = 'config.toml') -> None:
    """Load the config from the toml file. Supports both styles of config vars.

    Args:
        cfg: The OpenHandsConfig object to update attributes of.
        toml_file: The path to the toml file. Defaults to 'config.toml'.

    See Also:
    - config.template.toml for the full list of config options.
    """
    # try to read the config.toml file into the config object
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError:
        return
    except toml.TomlDecodeError as e:
        logger.openhands_logger.warning(
            f'Cannot parse config from toml, toml values have not been applied.\nError: {e}',
        )
        return

    # Check for the [core] section
    if 'core' not in toml_config:
        logger.openhands_logger.warning(
            f'No [core] section found in {toml_file}. Core settings will use defaults.'
        )
        core_config = {}
    else:
        core_config = toml_config['core']

    # Process core section if present
    for key, value in core_config.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        else:
            logger.openhands_logger.warning(
                f'Unknown config key "{key}" in [core] section'
            )

    # Process agent section if present
    if 'agent' in toml_config:
        try:
            agent_mapping = AgentConfig.from_toml_section(toml_config['agent'])
            for agent_key, agent_conf in agent_mapping.items():
                cfg.set_agent_config(agent_conf, agent_key)
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [agent] config from toml, values have not been applied.\nError: {e}'
            )

    # Process llm section if present
    if 'llm' in toml_config:
        try:
            llm_mapping = LLMConfig.from_toml_section(toml_config['llm'])
            for llm_key, llm_conf in llm_mapping.items():
                cfg.set_llm_config(llm_conf, llm_key)
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [llm] config from toml, values have not been applied.\nError: {e}'
            )

    # Process security section if present
    if 'security' in toml_config:
        try:
            security_mapping = SecurityConfig.from_toml_section(toml_config['security'])
            # We only use the base security config for now
            if 'security' in security_mapping:
                cfg.security = security_mapping['security']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [security] config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError:
            # Re-raise ValueError from SecurityConfig.from_toml_section
            raise ValueError('Error in [security] section in config.toml')

    # Process sandbox section if present
    if 'sandbox' in toml_config:
        try:
            sandbox_mapping = SandboxConfig.from_toml_section(toml_config['sandbox'])
            # We only use the base sandbox config for now
            if 'sandbox' in sandbox_mapping:
                cfg.sandbox = sandbox_mapping['sandbox']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [sandbox] config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError:
            # Re-raise ValueError from SandboxConfig.from_toml_section
            raise ValueError('Error in [sandbox] section in config.toml')

    # Process MCP sections if present
    if 'mcp' in toml_config:
        try:
            mcp_mapping = MCPConfig.from_toml_section(toml_config['mcp'])
            # We only use the base mcp config for now
            if 'mcp' in mcp_mapping:
                cfg.mcp = mcp_mapping['mcp']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse MCP config from toml, values have not been applied.\nError: {e}'
            )
        except ValueError:
            # Re-raise ValueError from MCPConfig.from_toml_section
            raise ValueError('Error in MCP sections in config.toml')

    # Process kubernetes section if present
    if 'kubernetes' in toml_config:
        try:
            kubernetes_mapping = KubernetesConfig.from_toml_section(
                toml_config['kubernetes']
            )
            if 'kubernetes' in kubernetes_mapping:
                cfg.kubernetes = kubernetes_mapping['kubernetes']
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [kubernetes] config from toml, values have not been applied.\nError: {e}'
            )

    # Process condenser section if present
    if 'condenser' in toml_config:
        try:
            # Pass the LLM configs to the condenser config parser
            condenser_mapping = condenser_config_from_toml_section(
                toml_config['condenser'], cfg.llms
            )
            # Assign the default condenser configuration to the default agent configuration
            if 'condenser' in condenser_mapping:
                # Get the default agent config and assign the condenser config to it
                default_agent_config = cfg.get_agent_config()
                default_agent_config.condenser = condenser_mapping['condenser']
                logger.openhands_logger.debug(
                    'Default condenser configuration loaded from config toml and assigned to default agent'
                )
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [condenser] config from toml, values have not been applied.\nError: {e}'
            )
    # If no condenser section is in toml but enable_default_condenser is True,
    # set LLMSummarizingCondenserConfig as default
    elif cfg.enable_default_condenser:
        from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig

        # Get default agent config
        default_agent_config = cfg.get_agent_config()

        # Create default LLM summarizing condenser config
        default_condenser = LLMSummarizingCondenserConfig(
            llm_config=cfg.get_llm_config(),  # Use default LLM config
            type='llm',
        )

        # Set as default condenser
        default_agent_config.condenser = default_condenser
        logger.openhands_logger.debug(
            'Default LLM summarizing condenser assigned to default agent (no condenser in config)'
        )

    # Process extended section if present
    if 'extended' in toml_config:
        try:
            cfg.extended = ExtendedConfig(toml_config['extended'])
        except (TypeError, KeyError, ValidationError) as e:
            logger.openhands_logger.warning(
                f'Cannot parse [extended] config from toml, values have not been applied.\nError: {e}'
            )

    # Check for unknown sections
    known_sections = {
        'core',
        'extended',
        'agent',
        'llm',
        'security',
        'sandbox',
        'condenser',
        'mcp',
        'kubernetes',
    }
    for key in toml_config:
        if key.lower() not in known_sections:
            logger.openhands_logger.warning(f'Unknown section [{key}] in {toml_file}')


def get_or_create_jwt_secret(file_store: FileStore) -> str:
    try:
        jwt_secret = file_store.read(JWT_SECRET)
        return jwt_secret
    except FileNotFoundError:
        new_secret = uuid4().hex
        file_store.write(JWT_SECRET, new_secret)
        return new_secret


def finalize_config(cfg: OpenHandsConfig) -> None:
    """More tweaks to the config after it's been loaded."""
    # Handle the sandbox.volumes parameter
    if cfg.workspace_base is not None or cfg.workspace_mount_path is not None:
        logger.openhands_logger.warning(
            'DEPRECATED: The WORKSPACE_BASE and WORKSPACE_MOUNT_PATH environment variables are deprecated. '
            "Please use RUNTIME_MOUNT instead, e.g. 'RUNTIME_MOUNT=/my/host/dir:/workspace:rw'"
        )
    if cfg.sandbox.volumes is not None:
        # Split by commas to handle multiple mounts
        mounts = cfg.sandbox.volumes.split(',')

        # Check if any mount explicitly targets /workspace
        workspace_mount_found = False
        for mount in mounts:
            parts = mount.split(':')
            if len(parts) >= 2 and parts[1] == '/workspace':
                workspace_mount_found = True
                host_path = os.path.abspath(parts[0])

                # Set the workspace_mount_path and workspace_mount_path_in_sandbox
                cfg.workspace_mount_path = host_path
                cfg.workspace_mount_path_in_sandbox = '/workspace'

                # Also set workspace_base
                cfg.workspace_base = host_path
                break

        # If no explicit /workspace mount was found, don't set any workspace mount
        # This allows users to mount volumes without affecting the workspace
        if not workspace_mount_found:
            logger.openhands_logger.debug(
                'No explicit /workspace mount found in SANDBOX_VOLUMES. '
                'Using default workspace path in sandbox.'
            )
            # Ensure workspace_mount_path and workspace_base are None to avoid
            # unintended mounting behavior
            cfg.workspace_mount_path = None
            cfg.workspace_base = None

        # Validate all mounts
        for mount in mounts:
            parts = mount.split(':')
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError(
                    f'Invalid mount format in sandbox.volumes: {mount}. '
                    f"Expected format: 'host_path:container_path[:mode]', e.g. '/my/host/dir:/workspace:rw'"
                )

    # Handle the deprecated workspace_* parameters
    elif cfg.workspace_base is not None or cfg.workspace_mount_path is not None:
        if cfg.workspace_base is not None:
            cfg.workspace_base = os.path.abspath(cfg.workspace_base)
            if cfg.workspace_mount_path is None:
                cfg.workspace_mount_path = cfg.workspace_base

        if cfg.workspace_mount_rewrite:
            base = cfg.workspace_base or os.getcwd()
            parts = cfg.workspace_mount_rewrite.split(':')
            cfg.workspace_mount_path = base.replace(parts[0], parts[1])

    # make sure log_completions_folder is an absolute path
    for llm in cfg.llms.values():
        llm.log_completions_folder = os.path.abspath(llm.log_completions_folder)

    if cfg.sandbox.use_host_network and platform.system() == 'Darwin':
        logger.openhands_logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )

    # make sure cache dir exists
    if cfg.cache_dir:
        pathlib.Path(cfg.cache_dir).mkdir(parents=True, exist_ok=True)

    if not cfg.jwt_secret:
        cfg.jwt_secret = SecretStr(
            get_or_create_jwt_secret(
                get_file_store(cfg.file_store, cfg.file_store_path)
            )
        )

    # If CLIRuntime is selected, disable Jupyter for all agents
    # Assuming 'cli' is the identifier for CLIRuntime
    if cfg.runtime and cfg.runtime.lower() == 'cli':
        for age_nt_name, agent_config in cfg.agents.items():
            if agent_config.enable_jupyter:
                agent_config.enable_jupyter = False
            if agent_config.enable_browsing:
                agent_config.enable_browsing = False
        logger.openhands_logger.debug(
            'Automatically disabled Jupyter plugin and browsing for all agents '
            'because CLIRuntime is selected and does not support IPython execution.'
        )


def get_agent_config_arg(
    agent_config_arg: str, toml_file: str = 'config.toml'
) -> AgentConfig | None:
    """Get a group of agent settings from the config file.

    A group in config.toml can look like this:

    ```
    [agent.default]
    enable_prompt_extensions = false
    ```

    The user-defined group name, like "default", is the argument to this function. The function will load the AgentConfig object
    with the settings of this group, from the config file, and set it as the AgentConfig object for the app.

    Note that the group must be under "agent" group, or in other words, the group name must start with "agent.".

    Args:
        agent_config_arg: The group of agent settings to get from the config.toml file.
        toml_file: Path to the configuration file to read from. Defaults to 'config.toml'.

    Returns:
        AgentConfig: The AgentConfig object with the settings from the config file.
    """
    # keep only the name, just in case
    agent_config_arg = agent_config_arg.strip('[]')

    # truncate the prefix, just in case
    if agent_config_arg.startswith('agent.'):
        agent_config_arg = agent_config_arg[6:]

    logger.openhands_logger.debug(f'Loading agent config from {agent_config_arg}')

    # load the toml file
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.openhands_logger.error(f'Config file not found: {e}')
        return None
    except toml.TomlDecodeError as e:
        logger.openhands_logger.error(
            f'Cannot parse agent group from {agent_config_arg}. Exception: {e}'
        )
        return None

    # update the agent config with the specified section
    if 'agent' in toml_config and agent_config_arg in toml_config['agent']:
        return AgentConfig(**toml_config['agent'][agent_config_arg])
    logger.openhands_logger.debug(f'Loading from toml failed for {agent_config_arg}')
    return None


def get_llm_config_arg(
    llm_config_arg: str, toml_file: str = 'config.toml'
) -> LLMConfig | None:
    """Get a group of llm settings from the config file.

    A group in config.toml can look like this:

    ```
    [llm.gpt-3.5-for-eval]
    model = 'gpt-3.5-turbo'
    api_key = '...'
    temperature = 0.5
    num_retries = 8
    ...
    ```

    The user-defined group name, like "gpt-3.5-for-eval", is the argument to this function. The function will load the LLMConfig object
    with the settings of this group, from the config file, and set it as the LLMConfig object for the app.

    Note that the group must be under "llm" group, or in other words, the group name must start with "llm.".

    Args:
        llm_config_arg: The group of llm settings to get from the config.toml file.
        toml_file: Path to the configuration file to read from. Defaults to 'config.toml'.

    Returns:
        LLMConfig: The LLMConfig object with the settings from the config file.
    """
    # keep only the name, just in case
    llm_config_arg = llm_config_arg.strip('[]')

    # truncate the prefix, just in case
    if llm_config_arg.startswith('llm.'):
        llm_config_arg = llm_config_arg[4:]

    logger.openhands_logger.debug(f'Loading llm config from {llm_config_arg}')

    # load the toml file
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.openhands_logger.error(f'Config file not found: {e}')
        return None
    except toml.TomlDecodeError as e:
        logger.openhands_logger.error(
            f'Cannot parse llm group from {llm_config_arg}. Exception: {e}'
        )
        return None

    # update the llm config with the specified section
    if 'llm' in toml_config and llm_config_arg in toml_config['llm']:
        return LLMConfig(**toml_config['llm'][llm_config_arg])
    logger.openhands_logger.debug(f'Loading from toml failed for {llm_config_arg}')
    return None


def get_condenser_config_arg(
    condenser_config_arg: str, toml_file: str = 'config.toml'
) -> CondenserConfig | None:
    """Get a group of condenser settings from the config file by name.

    A group in config.toml can look like this:

    ```
    [condenser.my_summarizer]
    type = 'llm'
    llm_config = 'gpt-4o' # References [llm.gpt-4o]
    max_size = 50
    ...
    ```

    The user-defined group name, like "my_summarizer", is the argument to this function.
    The function will load the CondenserConfig object with the settings of this group,
    from the config file.

    Note that the group must be under the "condenser" group, or in other words,
    the group name must start with "condenser.".

    Args:
        condenser_config_arg: The group of condenser settings to get from the config.toml file.
        toml_file: Path to the configuration file to read from. Defaults to 'config.toml'.

    Returns:
        CondenserConfig: The CondenserConfig object with the settings from the config file, or None if not found/error.
    """
    # keep only the name, just in case
    condenser_config_arg = condenser_config_arg.strip('[]')

    # truncate the prefix, just in case
    if condenser_config_arg.startswith('condenser.'):
        condenser_config_arg = condenser_config_arg[10:]

    logger.openhands_logger.debug(
        f'Loading condenser config [{condenser_config_arg}] from {toml_file}'
    )

    # load the toml file
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.openhands_logger.error(f'Config file not found: {toml_file}. Error: {e}')
        return None
    except toml.TomlDecodeError as e:
        logger.openhands_logger.error(
            f'Cannot parse condenser group [{condenser_config_arg}] from {toml_file}. Exception: {e}'
        )
        return None

    # Check if the condenser section and the specific config exist
    if (
        'condenser' not in toml_config
        or condenser_config_arg not in toml_config['condenser']
    ):
        logger.openhands_logger.error(
            f'Condenser config section [condenser.{condenser_config_arg}] not found in {toml_file}'
        )
        return None

    condenser_data = toml_config['condenser'][
        condenser_config_arg
    ].copy()  # Use copy to modify

    # Determine the type and handle potential LLM dependency
    condenser_type = condenser_data.get('type')
    if not condenser_type:
        logger.openhands_logger.error(
            f'Missing "type" field in [condenser.{condenser_config_arg}] section of {toml_file}'
        )
        return None

    # Handle LLM config reference if needed, using get_llm_config_arg
    if (
        condenser_type in ('llm', 'llm_attention', 'structured')
        and 'llm_config' in condenser_data
        and isinstance(condenser_data['llm_config'], str)
    ):
        llm_config_name = condenser_data['llm_config']
        logger.openhands_logger.debug(
            f'Condenser [{condenser_config_arg}] requires LLM config [{llm_config_name}]. Loading it...'
        )
        # Use the existing function to load the specific LLM config
        referenced_llm_config = get_llm_config_arg(llm_config_name, toml_file=toml_file)

        if referenced_llm_config:
            # Replace the string reference with the actual LLMConfig object
            condenser_data['llm_config'] = referenced_llm_config
        else:
            # get_llm_config_arg already logs the error if not found
            logger.openhands_logger.error(
                f"Failed to load required LLM config '{llm_config_name}' for condenser '{condenser_config_arg}'."
            )
            return None

    # Create the condenser config instance
    try:
        config = create_condenser_config(condenser_type, condenser_data)
        logger.openhands_logger.info(
            f'Successfully loaded condenser config [{condenser_config_arg}] from {toml_file}'
        )
        return config
    except (ValidationError, ValueError) as e:
        logger.openhands_logger.error(
            f'Invalid condenser configuration for [{condenser_config_arg}]: {e}.'
        )
        return None


# Command line arguments
def get_parser() -> argparse.ArgumentParser:
    """Get the argument parser."""
    parser = argparse.ArgumentParser(description='Run the agent via CLI')

    # Add version argument
    parser.add_argument(
        '-v', '--version', action='store_true', help='Show version information'
    )

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
    # --eval configs are for evaluations only
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
        help='Replace default LLM ([llm] section in config.toml) config with the specified LLM config, e.g. "llama3" for [llm.llama3] section in config.toml',
    )
    parser.add_argument(
        '--agent-config',
        default=None,
        type=str,
        help='Replace default Agent ([agent] section in config.toml) config with the specified Agent config, e.g. "CodeAct" for [agent.CodeAct] section in config.toml',
    )
    parser.add_argument(
        '-n',
        '--name',
        help='Session name',
        type=str,
        default='',
    )
    parser.add_argument(
        '--eval-ids',
        default=None,
        type=str,
        help='The comma-separated list (in quotes) of IDs of the instances to evaluate',
    )
    parser.add_argument(
        '--no-auto-continue',
        help='Disable auto-continue responses in headless mode (i.e. headless will read from stdin instead of auto-continuing)',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--selected-repo',
        help='GitHub repository to clone (format: owner/repo)',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--override-cli-mode',
        help='Override the default settings for CLI mode',
        type=bool,
        default=False,
    )
    parser.add_argument(
        '--log-level',
        help='Set the log level',
        type=str,
        default=None,
    )
    return parser


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = get_parser()
    args = parser.parse_args()

    if args.version:
        print(f'OpenHands version: {__version__}')
        sys.exit(0)

    return args


def register_custom_agents(config: OpenHandsConfig) -> None:
    """Register custom agents from configuration.

    This function is called after configuration is loaded to ensure all custom agents
    specified in the config are properly imported and registered.
    """
    # Import here to avoid circular dependency
    from openhands.controller.agent import Agent

    for agent_name, agent_config in config.agents.items():
        if agent_config.classpath:
            try:
                agent_cls = get_impl(Agent, agent_config.classpath)
                Agent.register(agent_name, agent_cls)
                logger.openhands_logger.info(
                    f"Registered custom agent '{agent_name}' from {agent_config.classpath}"
                )
            except Exception as e:
                logger.openhands_logger.error(
                    f"Failed to register agent '{agent_name}': {e}"
                )


def load_openhands_config(
    set_logging_levels: bool = True, config_file: str = 'config.toml'
) -> OpenHandsConfig:
    """Load the configuration from the specified config file and environment variables.

    Args:
        set_logging_levels: Whether to set the global variables for logging levels.
        config_file: Path to the config file. Defaults to 'config.toml' in the current directory.
    """
    config = OpenHandsConfig()
    load_from_toml(config, config_file)
    load_from_env(config, os.environ)
    finalize_config(config)
    register_custom_agents(config)
    if set_logging_levels:
        logger.DEBUG = config.debug
        logger.DISABLE_COLOR_PRINTING = config.disable_color
    return config


def setup_config_from_args(args: argparse.Namespace) -> OpenHandsConfig:
    """Load config from toml and override with command line arguments.

    Common setup used by both CLI and main.py entry points.
    """
    # Load base config from toml and env vars
    config = load_openhands_config(config_file=args.config_file)

    # Override with command line arguments if provided
    if args.llm_config:
        # if we didn't already load it, get it from the toml file
        if args.llm_config not in config.llms:
            llm_config = get_llm_config_arg(args.llm_config)
        else:
            llm_config = config.llms[args.llm_config]
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

    # Read selected repository in config for use by CLI and main.py
    if args.selected_repo is not None:
        config.sandbox.selected_repo = args.selected_repo

    return config
