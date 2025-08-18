from openhands.core.config import OpenHandsConfig
from openhands.runtime.plugins import PluginRequirement

DEFAULT_PYTHON_PREFIX = [
    '/openhands/micromamba/bin/micromamba',
    'run',
    '-n',
    'openhands',
    'poetry',
    'run',
]
DEFAULT_MAIN_MODULE = 'openhands.runtime.action_execution_server'


def get_action_execution_server_startup_command(
    server_port: int,
    plugins: list[PluginRequirement],
    app_config: OpenHandsConfig,
    python_prefix: list[str] = DEFAULT_PYTHON_PREFIX,
    override_user_id: int | None = None,
    override_username: str | None = None,
    main_module: str = DEFAULT_MAIN_MODULE,
    python_executable: str = 'python',
) -> list[str]:
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
    if app_config.run_as_openhands:
        resolved_uid = override_user_id if override_user_id is not None else sandbox_config.user_id
        # Avoid passing UID 0 for the non-root 'openhands' user inside containers
        # Fall back to 1000 when resolved UID is 0 or None
        user_id = resolved_uid if resolved_uid not in (None, 0) else 1000
    else:
        user_id = 0

    base_cmd = [
        *python_prefix,
        python_executable,
        '-u',
        '-m',
        main_module,
        str(server_port),
        '--working-dir',
        app_config.workspace_mount_path_in_sandbox,
        *plugin_args,
        '--username',
        username,
        '--user-id',
        str(user_id),
        '--git-user-name',
        app_config.git_user_name,
        '--git-user-email',
        app_config.git_user_email,
        *browsergym_args,
    ]

    if not app_config.enable_browser:
        base_cmd.append('--no-enable-browser')

    return base_cmd
