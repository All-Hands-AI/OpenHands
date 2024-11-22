def get_remote_startup_command(
    port: int,
    sandbox_workspace_dir: str,
    username: str,
    user_id: int,
    plugin_args: list[str],
    browsergym_args: list[str],
):
    cmd = f'/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server {port} --working-dir {sandbox_workspace_dir} {" ".join(plugin_args)} --username {username} --user-id {user_id} {" ".join(browsergym_args)}'
    return [
        'sudo',  # Needed for nice -20
        'nice',
        '-n',
        '-20',  # Highest priority
        'sh',
        '-c',
        f'echo -1000 > /proc/self/oom_score_adj && exec {cmd}'
    ]
