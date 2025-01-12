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
    use_nice_for_root: bool = True,
):
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

    is_root = not app_config.run_as_openhands

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
        'openhands' if app_config.run_as_openhands else 'root',
        '--user-id',
        str(sandbox_config.user_id),
        *browsergym_args,
    ]

    if is_root and use_nice_for_root:
        # If running as root, set highest priority and lowest OOM score
        cmd_str = ' '.join(base_cmd)
        return [
            'nice',
            '-n',
            '-20',  # Highest priority
            'sh',
            '-c',
            f'echo -1000 > /proc/self/oom_score_adj && exec {cmd_str}',
        ]
    else:
        # If not root OR not using nice for root, run with normal priority
        return base_cmd
