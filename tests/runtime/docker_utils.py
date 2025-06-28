"""Utility functions for Docker-related tests."""

import subprocess


def is_docker_available() -> tuple[bool, str]:
    """Check if Docker is available and running.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if Docker is available
                         and a string with the reason if it's not.
    """
    try:
        # Check if Docker CLI is installed
        result = subprocess.run(
            ['docker', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, 'Docker CLI is not installed or not in PATH'

        # Check if Docker daemon is running
        result = subprocess.run(
            ['docker', 'info'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, 'Docker daemon is not running'

        return True, ''
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return False, f'Error checking Docker: {str(e)}'
