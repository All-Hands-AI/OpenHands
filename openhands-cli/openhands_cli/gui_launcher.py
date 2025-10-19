"""GUI launcher for OpenHands CLI."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from openhands_cli.locations import PERSISTENCE_DIR


def _format_docker_command_for_logging(cmd: list[str]) -> str:
    """Format a Docker command for logging with grey color.

    Args:
        cmd (list[str]): The Docker command as a list of strings

    Returns:
        str: The formatted command string in grey HTML color
    """
    cmd_str = ' '.join(cmd)
    return f'<grey>Running Docker command: {cmd_str}</grey>'


def check_docker_requirements() -> bool:
    """Check if Docker is installed and running.

    Returns:
        bool: True if Docker is available and running, False otherwise.
    """
    # Check if Docker is installed
    if not shutil.which('docker'):
        print_formatted_text(
            HTML('<ansired>❌ Docker is not installed or not in PATH.</ansired>')
        )
        print_formatted_text(
            HTML(
                '<grey>Please install Docker first: https://docs.docker.com/get-docker/</grey>'
            )
        )
        return False

    # Check if Docker daemon is running
    try:
        result = subprocess.run(
            ['docker', 'info'], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print_formatted_text(
                HTML('<ansired>❌ Docker daemon is not running.</ansired>')
            )
            print_formatted_text(
                HTML('<grey>Please start Docker and try again.</grey>')
            )
            return False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        print_formatted_text(
            HTML('<ansired>❌ Failed to check Docker status.</ansired>')
        )
        print_formatted_text(HTML(f'<grey>Error: {e}</grey>'))
        return False

    return True


def ensure_config_dir_exists() -> Path:
    """Ensure the OpenHands configuration directory exists and return its path."""
    path = Path(PERSISTENCE_DIR)
    path.mkdir(exist_ok=True, parents=True)
    return path


def get_openhands_version() -> str:
    """Get the OpenHands version for Docker images.

    Returns:
        str: The version string to use for Docker images
    """
    # For now, use 'latest' as the default version
    # In the future, this could be read from a version file or environment variable
    return os.environ.get('OPENHANDS_VERSION', 'latest')


def launch_gui_server(mount_cwd: bool = False, gpu: bool = False) -> None:
    """Launch the OpenHands GUI server using Docker.

    Args:
        mount_cwd: If True, mount the current working directory into the container.
        gpu: If True, enable GPU support by mounting all GPUs into the container via nvidia-docker.
    """
    print_formatted_text(
        HTML('<ansiblue>🚀 Launching OpenHands GUI server...</ansiblue>')
    )
    print_formatted_text('')

    # Check Docker requirements
    if not check_docker_requirements():
        sys.exit(1)

    # Ensure config directory exists
    config_dir = ensure_config_dir_exists()

    # Get the current version for the Docker image
    version = get_openhands_version()
    runtime_image = f'docker.all-hands.dev/openhands/runtime:{version}-nikolaik'
    app_image = f'docker.all-hands.dev/openhands/openhands:{version}'

    print_formatted_text(HTML('<grey>Pulling required Docker images...</grey>'))

    # Pull the runtime image first
    pull_cmd = ['docker', 'pull', runtime_image]
    print_formatted_text(HTML(_format_docker_command_for_logging(pull_cmd)))
    try:
        subprocess.run(pull_cmd, check=True)
    except subprocess.CalledProcessError:
        print_formatted_text(
            HTML('<ansired>❌ Failed to pull runtime image.</ansired>')
        )
        sys.exit(1)

    print_formatted_text('')
    print_formatted_text(
        HTML('<ansigreen>✅ Starting OpenHands GUI server...</ansigreen>')
    )
    print_formatted_text(
        HTML('<grey>The server will be available at: http://localhost:3000</grey>')
    )
    print_formatted_text(HTML('<grey>Press Ctrl+C to stop the server.</grey>'))
    print_formatted_text('')

    # Build the Docker command
    docker_cmd = [
        'docker',
        'run',
        '-it',
        '--rm',
        '--pull=always',
        '-e',
        f'SANDBOX_RUNTIME_CONTAINER_IMAGE={runtime_image}',
        '-e',
        'LOG_ALL_EVENTS=true',
        '-v',
        '/var/run/docker.sock:/var/run/docker.sock',
        '-v',
        f'{config_dir}:/.openhands',
    ]

    # Add GPU support if requested
    if gpu:
        print_formatted_text(
            HTML('<ansigreen>🖥️ Enabling GPU support via nvidia-docker...</ansigreen>')
        )
        # Add the --gpus all flag to enable all GPUs
        docker_cmd.insert(2, '--gpus')
        docker_cmd.insert(3, 'all')
        # Add environment variable to pass GPU support to sandbox containers
        docker_cmd.extend(
            [
                '-e',
                'SANDBOX_ENABLE_GPU=true',
            ]
        )

    # Add current working directory mount if requested
    if mount_cwd:
        cwd = Path.cwd()
        # Following the documentation at https://docs.all-hands.dev/usage/runtimes/docker#connecting-to-your-filesystem
        docker_cmd.extend(
            [
                '-e',
                f'SANDBOX_VOLUMES={cwd}:/workspace:rw',
            ]
        )

        # Set user ID for Unix-like systems only
        if os.name != 'nt':  # Not Windows
            try:
                user_id = subprocess.check_output(['id', '-u'], text=True).strip()
                docker_cmd.extend(['-e', f'SANDBOX_USER_ID={user_id}'])
            except (subprocess.CalledProcessError, FileNotFoundError):
                # If 'id' command fails or doesn't exist, skip setting user ID
                pass
        # Print the folder that will be mounted to inform the user
        print_formatted_text(
            HTML(
                f'<ansigreen>📂 Mounting current directory:</ansigreen> <ansiyellow>{cwd}</ansiyellow> <ansigreen>to</ansigreen> <ansiyellow>/workspace</ansiyellow>'
            )
        )

    docker_cmd.extend(
        [
            '-p',
            '3000:3000',
            '--add-host',
            'host.docker.internal:host-gateway',
            '--name',
            'openhands-app',
            app_image,
        ]
    )

    try:
        # Log and run the Docker command
        print_formatted_text(HTML(_format_docker_command_for_logging(docker_cmd)))
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print_formatted_text('')
        print_formatted_text(
            HTML('<ansired>❌ Failed to start OpenHands GUI server.</ansired>')
        )
        print_formatted_text(HTML(f'<grey>Error: {e}</grey>'))
        sys.exit(1)
    except KeyboardInterrupt:
        print_formatted_text('')
        print_formatted_text(
            HTML('<ansigreen>✓ OpenHands GUI server stopped successfully.</ansigreen>')
        )
        sys.exit(0)
