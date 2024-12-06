def get_remote_startup_command(
    port: int,
    sandbox_workspace_dir: str,
    username: str,
    user_id: int,
    plugin_args: list[str],
    browsergym_args: list[str],
    is_root: bool = False,
):
    base_cmd = [
        '/openhands/micromamba/bin/micromamba',
        'run',
        '-n',
        'openhands',
        'poetry',
        'run',
        'python',
        '-u',
        '-m',
        'openhands.runtime.action_execution_server',
        str(port),
        '--working-dir',
        sandbox_workspace_dir,
        *plugin_args,
        '--username',
        username,
        '--user-id',
        str(user_id),
        *browsergym_args,
    ]

    if is_root:
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
        # If not root, run with normal priority
        return base_cmd
