"""GUI launcher for OpenHands CLI."""

import shutil
import subprocess
import sys
from pathlib import Path

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands import __version__


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


def get_openhands_config_dir() -> Path:
    """Get the OpenHands configuration directory path.

    Returns:
        Path: Path to the ~/.openhands directory.
    """
    return Path.home() / '.openhands'


def ensure_config_dir_exists() -> None:
    """Ensure the OpenHands configuration directory exists."""
    config_dir = get_openhands_config_dir()
    config_dir.mkdir(exist_ok=True)


def launch_gui_server(
    dry_run: bool = False, mount_cwd: bool = False, gpu: bool = False
) -> None:
    """Launch the OpenHands GUI server using Docker.

    Args:
        dry_run: If True, only show what would be executed without running it.
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
    ensure_config_dir_exists()
    config_dir = get_openhands_config_dir()

    # Get the current version for the Docker image
    version = __version__
    runtime_image = f'docker.all-hands.dev/all-hands-ai/runtime:{version}-nikolaik'
    app_image = f'docker.all-hands.dev/all-hands-ai/openhands:{version}'

    if dry_run:
        print_formatted_text(
            HTML(
                '<ansiyellow>🧪 DRY RUN MODE - Commands will not be executed</ansiyellow>'
            )
        )
        print_formatted_text('')

    print_formatted_text(HTML('<grey>Pulling required Docker images...</grey>'))

    # Pull the runtime image first
    pull_cmd = ['docker', 'pull', runtime_image]
    if dry_run:
        print_formatted_text(HTML(f'<grey>Would run: {" ".join(pull_cmd)}</grey>'))
    else:
        try:
            subprocess.run(
                pull_cmd,
                check=True,
                timeout=300,  # 5 minutes timeout
            )
        except subprocess.CalledProcessError:
            print_formatted_text(
                HTML('<ansired>❌ Failed to pull runtime image.</ansired>')
            )
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print_formatted_text(
                HTML('<ansired>❌ Timeout while pulling runtime image.</ansired>')
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

    # Add current working directory mount if requested
    if mount_cwd:
        cwd = Path.cwd()
        # Following the documentation at https://docs.all-hands.dev/usage/runtimes/docker#connecting-to-your-filesystem
        docker_cmd.extend(
            [
                '-e',
                f'SANDBOX_VOLUMES={cwd}:/workspace:rw',
                '-e',
                f'SANDBOX_USER_ID={subprocess.check_output(["id", "-u"], text=True).strip()}',
            ]
        )
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

    if dry_run:
        print_formatted_text(HTML(f'<grey>Would run: {" ".join(docker_cmd)}</grey>'))
        print_formatted_text('')
        print_formatted_text(
            HTML('<ansigreen>✅ Dry run completed successfully!</ansigreen>')
        )
        return

    try:
        # Run the Docker command
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
