import os
import subprocess


def run_cmd(cmd: str, cwd: str | None = None) -> str | None:
    """Run a command and return the output.

    If the command succeeds, return None. If the command fails, return the stdout.
    """

    process = subprocess.Popen(
        cmd.split(),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8',
        errors='replace',
    )
    stdout, _ = process.communicate()
    if process.returncode == 0:
        return None
    return stdout


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run(
            [tool_name, '--version'],
            check=True,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
