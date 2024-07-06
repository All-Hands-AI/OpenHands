import argparse
import logging
import os
import pathlib
import platform
import uuid
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, ClassVar, MutableMapping, get_args, get_origin

import toml
from dotenv import load_dotenv

from opendevin.core.utils import Singleton

logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class LLMConfig(metaclass=Singleton):
    """
    Configuration for the LLM model.

    Attributes:
        model: The model to use.
        api_key: The API key to use.
        base_url: The base URL for the API. This is necessary for local LLMs. It is also used for Azure embeddings.
        api_version: The version of the API.
        embedding_model: The embedding model to use.
        embedding_base_url: The base URL for the embedding API.
        embedding_deployment_name: The name of the deployment for the embedding API. This is used for Azure OpenAI.
        aws_access_key_id: The AWS access key ID.
        aws_secret_access_key: The AWS secret access key.
        aws_region_name: The AWS region name.
        num_retries: The number of retries to attempt.
        retry_min_wait: The minimum time to wait between retries, in seconds. This is exponential backoff minimum. For models with very low limits, this can be set to 15-20.
        retry_max_wait: The maximum time to wait between retries, in seconds. This is exponential backoff maximum.
        timeout: The timeout for the API.
        max_message_chars: The approximate max number of characters in the content of an event included in the prompt to the LLM. Larger observations are truncated.
        temperature: The temperature for the API.
        top_p: The top p for the API.
        custom_llm_provider: The custom LLM provider to use. This is undocumented in opendevin, and normally not used. It is documented on the litellm side.
        max_input_tokens: The maximum number of input tokens. Note that this is currently unused, and the value at runtime is actually the total tokens in OpenAI (e.g. 128,000 tokens for GPT-4).
        max_output_tokens: The maximum number of output tokens. This is sent to the LLM.
        input_cost_per_token: The cost per input token. This will available in logs for the user to check.
        output_cost_per_token: The cost per output token. This will available in logs for the user to check.
        ollama_base_url: The base URL for the OLLAMA API.
    """

    model: str = 'gpt-4o'
    api_key: str | None = None
    base_url: str | None = None
    api_version: str | None = None
    embedding_model: str = 'local'
    embedding_base_url: str | None = None
    embedding_deployment_name: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region_name: str | None = None
    num_retries: int = 5
    retry_min_wait: int = 3
    retry_max_wait: int = 60
    timeout: int | None = None
    max_message_chars: int = 10_000  # maximum number of characters in an observation's content when sent to the llm
    temperature: float = 0
    top_p: float = 0.5
    custom_llm_provider: str | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    ollama_base_url: str | None = None

    def defaults_to_dict(self) -> dict:
        """
        Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional.
        """
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            if attr_name in ['api_key', 'aws_access_key_id', 'aws_secret_access_key']:
                attr_value = '******' if attr_value else None

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"LLMConfig({', '.join(attr_str)})"

    def __repr__(self):
        return self.__str__()


@dataclass
class AgentConfig(metaclass=Singleton):
    """
    Configuration for the agent.

    Attributes:
        name: The name of the agent.
        memory_enabled: Whether long-term memory (embeddings) is enabled.
        memory_max_threads: The maximum number of threads indexing at the same time for embeddings.
    """

    name: str = 'CodeActAgent'
    memory_enabled: bool = False
    memory_max_threads: int = 2

    def defaults_to_dict(self) -> dict:
        """
        Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional.
        """
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result


@dataclass
class SandboxConfig(metaclass=Singleton):
    """
    Configuration for the sandbox.

    Attributes:
        box_type: The type of sandbox to use. Options are: ssh, e2b, local.
        container_image: The container image to use for the sandbox.
        user_id: The user ID for the sandbox.
        timeout: The timeout for the sandbox.

    """

    box_type: str = 'ssh'
    container_image: str = 'ghcr.io/opendevin/sandbox' + (
        f':{os.getenv("OPEN_DEVIN_BUILD_VERSION")}'
        if os.getenv('OPEN_DEVIN_BUILD_VERSION')
        else ':main'
    )
    user_id: int = os.getuid() if hasattr(os, 'getuid') else 1000
    timeout: int = 120

    def defaults_to_dict(self) -> dict:
        """
        Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional.
        """
        dict = {}
        for f in fields(self):
            dict[f.name] = get_field_info(f)
        return dict

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"SandboxConfig({', '.join(attr_str)})"

    def __repr__(self):
        return self.__str__()


class UndefinedString(str, Enum):
    UNDEFINED = 'UNDEFINED'


@dataclass
class AppConfig(metaclass=Singleton):
    """
    Configuration for the app.

    Attributes:
        llm: The LLM configuration.
        agent: The agent configuration.
        sandbox: The sandbox configuration.
        runtime: The runtime environment.
        file_store: The file store to use.
        file_store_path: The path to the file store.
        workspace_base: The base path for the workspace. Defaults to ./workspace as an absolute path.
        workspace_mount_path: The path to mount the workspace. This is set to the workspace base by default.
        workspace_mount_path_in_sandbox: The path to mount the workspace in the sandbox. Defaults to /workspace.
        workspace_mount_rewrite: The path to rewrite the workspace mount path to.
        cache_dir: The path to the cache directory. Defaults to /tmp/cache.
        run_as_devin: Whether to run as devin.
        max_iterations: The maximum number of iterations.
        max_budget_per_task: The maximum budget allowed per task, beyond which the agent will stop.
        e2b_api_key: The E2B API key.
        use_host_network: Whether to use the host network.
        ssh_hostname: The SSH hostname.
        disable_color: Whether to disable color. For terminals that don't support color.
        initialize_plugins: Whether to initialize plugins.
        debug: Whether to enable debugging.
        enable_auto_lint: Whether to enable auto linting. This is False by default, for regular runs of the app. For evaluation, please set this to True.
        enable_cli_session: Whether to enable saving and restoring the session when run from CLI.
        file_uploads_max_file_size_mb: Maximum file size for uploads in megabytes. 0 means no limit.
        file_uploads_restrict_file_types: Whether to restrict file types for file uploads. Defaults to False.
        file_uploads_allowed_extensions: List of allowed file extensions for uploads. ['.*'] means all extensions are allowed.
    """

    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    runtime: str = 'server'
    file_store: str = 'memory'
    file_store_path: str = '/tmp/file_store'
    workspace_base: str = os.path.join(os.getcwd(), 'workspace')
    workspace_mount_path: str = (
        UndefinedString.UNDEFINED  # this path should always be set when config is fully loaded
    )
    workspace_mount_path_in_sandbox: str = '/workspace'
    workspace_mount_rewrite: str | None = None
    cache_dir: str = '/tmp/cache'
    run_as_devin: bool = True
    max_iterations: int = 100
    max_budget_per_task: float | None = None
    e2b_api_key: str = ''
    use_host_network: bool = False
    ssh_hostname: str = 'localhost'
    disable_color: bool = False
    initialize_plugins: bool = True
    persist_sandbox: bool = False
    ssh_port: int = 63710
    ssh_password: str | None = None
    jwt_secret: str = uuid.uuid4().hex
    debug: bool = False
    enable_auto_lint: bool = (
        False  # once enabled, OpenDevin would lint files after editing
    )
    enable_cli_session: bool = False
    file_uploads_max_file_size_mb: int = 0
    file_uploads_restrict_file_types: bool = False
    file_uploads_allowed_extensions: list[str] = field(default_factory=lambda: ['.*'])

    defaults_dict: ClassVar[dict] = {}

    def __post_init__(self):
        """
        Post-initialization hook, called when the instance is created with only default values.
        """
        AppConfig.defaults_dict = self.defaults_to_dict()

    def defaults_to_dict(self) -> dict:
        """
        Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional.
        """
        result = {}
        for f in fields(self):
            field_value = getattr(self, f.name)

            # dataclasses compute their defaults themselves
            if is_dataclass(type(field_value)):
                result[f.name] = field_value.defaults_to_dict()
            else:
                result[f.name] = get_field_info(f)
        return result

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            if attr_name in [
                'e2b_api_key',
                'github_token',
                'jwt_secret',
                'ssh_password',
            ]:
                attr_value = '******' if attr_value else None

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"AppConfig({', '.join(attr_str)}"

    def __repr__(self):
        return self.__str__()


def get_field_info(f):
    """
    Extract information about a dataclass field: type, optional, and default.

    Args:
        f: The field to extract information from.

    Returns: A dict with the field's type, whether it's optional, and its default value.
    """
    field_type = f.type
    optional = False

    # for types like str | None, find the non-None type and set optional to True
    # this is useful for the frontend to know if a field is optional
    # and to show the correct type in the UI
    # Note: this only works for UnionTypes with None as one of the types
    if get_origin(field_type) is UnionType:
        types = get_args(field_type)
        non_none_arg = next((t for t in types if t is not type(None)), None)
        if non_none_arg is not None:
            field_type = non_none_arg
            optional = True

    # type name in a pretty format
    type_name = (
        field_type.__name__ if hasattr(field_type, '__name__') else str(field_type)
    )

    # default is always present
    default = f.default

    # return a schema with the useful info for frontend
    return {'type': type_name.lower(), 'optional': optional, 'default': default}


def load_from_env(cfg: AppConfig, env_or_toml_dict: dict | MutableMapping[str, str]):
    """Reads the env-style vars and sets config attributes based on env vars or a config.toml dict.
    Compatibility with vars like LLM_BASE_URL, AGENT_MEMORY_ENABLED, SANDBOX_TIMEOUT and others.

    Args:
        cfg: The AppConfig object to set attributes on.
        env_or_toml_dict: The environment variables or a config.toml dict.
    """

    def get_optional_type(union_type: UnionType) -> Any:
        """Returns the non-None type from a Union."""
        types = get_args(union_type)
        return next((t for t in types if t is not type(None)), None)

    # helper function to set attributes based on env vars
    def set_attr_from_env(sub_config: Any, prefix=''):
        """Set attributes of a config dataclass based on environment variables."""
        for field_name, field_type in sub_config.__annotations__.items():
            # compute the expected env var name from the prefix and field name
            # e.g. LLM_BASE_URL
            env_var_name = (prefix + field_name).upper()

            if is_dataclass(field_type):
                # nested dataclass
                nested_sub_config = getattr(sub_config, field_name)

                # the agent field: the env var for agent.name is just 'AGENT'
                if field_name == 'agent' and 'AGENT' in env_or_toml_dict:
                    setattr(nested_sub_config, 'name', env_or_toml_dict[env_var_name])

                set_attr_from_env(nested_sub_config, prefix=field_name + '_')
            elif env_var_name in env_or_toml_dict:
                # convert the env var to the correct type and set it
                value = env_or_toml_dict[env_var_name]
                try:
                    # if it's an optional type, get the non-None type
                    if get_origin(field_type) is UnionType:
                        field_type = get_optional_type(field_type)

                    # Attempt to cast the env var to type hinted in the dataclass
                    if field_type is bool:
                        cast_value = str(value).lower() in ['true', '1']
                    else:
                        cast_value = field_type(value)
                    setattr(sub_config, field_name, cast_value)
                except (ValueError, TypeError):
                    logger.error(
                        f'Error setting env var {env_var_name}={value}: check that the value is of the right type'
                    )

    if 'SANDBOX_TYPE' in env_or_toml_dict:
        logger.error('SANDBOX_TYPE is deprecated. Please use SANDBOX_BOX_TYPE instead.')
        env_or_toml_dict['SANDBOX_BOX_TYPE'] = env_or_toml_dict.pop('SANDBOX_TYPE')
    # Start processing from the root of the config object
    set_attr_from_env(cfg)


def load_from_toml(cfg: AppConfig, toml_file: str = 'config.toml'):
    """Load the config from the toml file. Supports both styles of config vars.

    Args:
        cfg: The AppConfig object to update attributes of.
        toml_file: The path to the toml file. Defaults to 'config.toml'.
    """

    # try to read the config.toml file into the config object
    try:
        with open(toml_file, 'r', encoding='utf-8') as toml_contents:
            toml_config = toml.load(toml_contents)
    except FileNotFoundError as e:
        logger.info(f'Config file not found: {e}')
        return
    except toml.TomlDecodeError as e:
        logger.warning(
            f'Cannot parse config from toml, toml values have not been applied.\nError: {e}',
            exc_info=False,
        )
        return

    # if there was an exception or core is not in the toml, try to use the old-style toml
    if 'core' not in toml_config:
        # re-use the env loader to set the config from env-style vars
        load_from_env(cfg, toml_config)
        return

    core_config = toml_config['core']

    try:
        # set llm config from the toml file
        llm_config = cfg.llm
        if 'llm' in toml_config:
            llm_config = LLMConfig(**toml_config['llm'])

        # set agent config from the toml file
        agent_config = cfg.agent
        if 'agent' in toml_config:
            agent_config = AgentConfig(**toml_config['agent'])

        # set sandbox config from the toml file
        sandbox_config = config.sandbox

        # migrate old sandbox configs from [core] section to sandbox config
        keys_to_migrate = [key for key in core_config if key.startswith('sandbox_')]
        for key in keys_to_migrate:
            new_key = key.replace('sandbox_', '')
            if new_key == 'type':
                new_key = 'box_type'
            if new_key in sandbox_config.__annotations__:
                # read the key in sandbox and remove it from core
                setattr(sandbox_config, new_key, core_config.pop(key))
            else:
                logger.warning(f'Unknown sandbox config: {key}')

        # the new style values override the old style values
        if 'sandbox' in toml_config:
            sandbox_config = SandboxConfig(**toml_config['sandbox'])

        # update the config object with the new values
        AppConfig(
            llm=llm_config,
            agent=agent_config,
            sandbox=sandbox_config,
            **core_config,
        )
    except (TypeError, KeyError) as e:
        logger.warning(
            f'Cannot parse config from toml, toml values have not been applied.\nError: {e}',
            exc_info=False,
        )


def finalize_config(cfg: AppConfig):
    """
    More tweaks to the config after it's been loaded.
    """

    # Set workspace_mount_path if not set by the user
    if cfg.workspace_mount_path is UndefinedString.UNDEFINED:
        cfg.workspace_mount_path = os.path.abspath(cfg.workspace_base)
    cfg.workspace_base = os.path.abspath(cfg.workspace_base)

    # In local there is no sandbox, the workspace will have the same pwd as the host
    if cfg.sandbox.box_type == 'local':
        cfg.workspace_mount_path_in_sandbox = cfg.workspace_mount_path

    if cfg.workspace_mount_rewrite:  # and not config.workspace_mount_path:
        # TODO why do we need to check if workspace_mount_path is None?
        base = cfg.workspace_base or os.getcwd()
        parts = cfg.workspace_mount_rewrite.split(':')
        cfg.workspace_mount_path = base.replace(parts[0], parts[1])

    if cfg.llm.embedding_base_url is None:
        cfg.llm.embedding_base_url = cfg.llm.base_url

    if cfg.use_host_network and platform.system() == 'Darwin':
        logger.warning(
            'Please upgrade to Docker Desktop 4.29.0 or later to use host network mode on macOS. '
            'See https://github.com/docker/roadmap/issues/238#issuecomment-2044688144 for more information.'
        )

    # make sure cache dir exists
    if cfg.cache_dir:
        pathlib.Path(cfg.cache_dir).mkdir(parents=True, exist_ok=True)


config = AppConfig()
load_from_toml(config)
load_from_env(config, os.environ)
finalize_config(config)


# Utility function for command line --group argument
def get_llm_config_arg(llm_config_arg: str):
    """
    Get a group of llm settings from the config file.

    A group in config.toml can look like this:

    ```
    [gpt-3.5-for-eval]
    model = 'gpt-3.5-turbo'
    api_key = '...'
    temperature = 0.5
    num_retries = 10
    ...
    ```

    The user-defined group name, like "gpt-3.5-for-eval", is the argument to this function. The function will load the LLMConfig object
    with the settings of this group, from the config file, and set it as the LLMConfig object for the app.

    Args:
        llm_config_arg: The group of llm settings to get from the config.toml file.

    Returns:
        LLMConfig: The LLMConfig object with the settings from the config file.
    """

    # keep only the name, just in case
    llm_config_arg = llm_config_arg.strip('[]')
    logger.info(f'Loading llm config from {llm_config_arg}')

    # load the toml file
    try:
        with open('config.toml', 'r', encoding='utf-8') as toml_file:
            toml_config = toml.load(toml_file)
    except FileNotFoundError as e:
        logger.error(f'Config file not found: {e}')
        return None
    except toml.TomlDecodeError as e:
        logger.error(f'Cannot parse llm group from {llm_config_arg}. Exception: {e}')
        return None

    # update the llm config with the specified section
    if llm_config_arg in toml_config:
        return LLMConfig(**toml_config[llm_config_arg])
    logger.debug(f'Loading from toml failed for {llm_config_arg}')
    return None


# Command line arguments
def get_parser() -> argparse.ArgumentParser:
    """
    Get the parser for the command line arguments.
    """
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
        '-b',
        '--max-budget-per-task',
        default=config.max_budget_per_task,
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
        help='The group of llm settings, e.g. a [llama3] section in the toml file. Overrides model if both are provided.',
    )
    return parser


def parse_arguments() -> argparse.Namespace:
    """
    Parse the command line arguments.
    """
    parser = get_parser()
    parsed_args, _ = parser.parse_known_args()
    if parsed_args.directory:
        config.workspace_base = os.path.abspath(parsed_args.directory)
        print(f'Setting workspace base to {config.workspace_base}')
    return parsed_args
