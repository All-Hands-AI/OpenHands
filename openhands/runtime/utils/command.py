import warnings

from openhands.core.config import AppConfig
from openhands.runtime.plugins import PluginRequirement

DEFAULT_PYTHON_PREFIX = [
    '/openhands/micromamba/bin/micromamba',
    'run',
    '-n',
    'openhands',
    'poetry',
    'run',
]


def get_action_execution_server_startup_command(
    server_port: int,
    plugins: list[PluginRequirement],
    app_config: AppConfig,
    python_prefix: list[str] = DEFAULT_PYTHON_PREFIX,
    override_user_id: int | None = None,
    override_username: str | None = None,
) -> list[str]:
    """
    DEPRECATED: This function has been moved to a method on the DockerRuntime class.
    Use DockerRuntime.get_action_execution_server_startup_command() instead.

    This function will be removed in a future release.
    """
    warnings.warn(
        'get_action_execution_server_startup_command is deprecated. '
        'Use DockerRuntime.get_action_execution_server_startup_command() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    sandbox_config = app_config.sandbox

    # Plugin args
    plugin_args = []
    if plugins is not None and len(plugins) > 0:
        plugin_args = ['--plugins'] + [plugin.name for plugin in plugins]

    # Browsergym stuffs
    browsergym_args = []
    if sandbox_config.browsergym_eval_env is not None:
        browsergym_args = [
            '--browsergym-eval-env'
        ] + sandbox_config.browsergym_eval_env.split(' ')

    username = override_username or (
        'openhands' if app_config.run_as_openhands else 'root'
    )
    user_id = override_user_id or (
        sandbox_config.user_id if app_config.run_as_openhands else 0
    )

    base_cmd = [
        *python_prefix,
        'python',
        '-u',
        '-m',
        'openhands.runtime.action_execution_server',
        str(server_port),
        '--working-dir',
        app_config.workspace_mount_path_in_sandbox,
        *plugin_args,
        '--username',
        username,
        '--user-id',
        str(user_id),
        *browsergym_args,
    ]

    return base_cmd
