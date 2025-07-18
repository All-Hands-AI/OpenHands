"""Tests for the CLI UI launcher functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openhands.cli.ui_launcher import (
    check_docker_requirements,
    ensure_config_dir_exists,
    get_openhands_config_dir,
    launch_ui_server,
)


class TestDockerRequirements:
    """Test Docker requirements checking."""

    @patch('openhands.cli.ui_launcher.shutil.which')
    def test_check_docker_requirements_no_docker(self, mock_which):
        """Test Docker requirements check when Docker is not installed."""
        mock_which.return_value = None

        with patch('openhands.cli.ui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()

        assert result is False
        mock_print.assert_called()

    @patch('openhands.cli.ui_launcher.shutil.which')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    def test_check_docker_requirements_daemon_not_running(self, mock_run, mock_which):
        """Test Docker requirements check when Docker daemon is not running."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.return_value = MagicMock(returncode=1)

        with patch('openhands.cli.ui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()

        assert result is False
        mock_print.assert_called()
        mock_run.assert_called_once_with(
            ['docker', 'info'], capture_output=True, text=True, timeout=10
        )

    @patch('openhands.cli.ui_launcher.shutil.which')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    def test_check_docker_requirements_timeout(self, mock_run, mock_which):
        """Test Docker requirements check when Docker command times out."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.side_effect = subprocess.TimeoutExpired('docker', 10)

        with patch('openhands.cli.ui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()

        assert result is False
        mock_print.assert_called()

    @patch('openhands.cli.ui_launcher.shutil.which')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    def test_check_docker_requirements_success(self, mock_run, mock_which):
        """Test Docker requirements check when Docker is available and running."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.return_value = MagicMock(returncode=0)

        result = check_docker_requirements()

        assert result is True
        mock_run.assert_called_once_with(
            ['docker', 'info'], capture_output=True, text=True, timeout=10
        )


class TestConfigDirectory:
    """Test configuration directory handling."""

    def test_get_openhands_config_dir(self):
        """Test getting the OpenHands config directory path."""
        config_dir = get_openhands_config_dir()

        assert isinstance(config_dir, Path)
        assert config_dir.name == '.openhands'
        assert config_dir.parent == Path.home()

    @patch('openhands.cli.ui_launcher.get_openhands_config_dir')
    def test_ensure_config_dir_exists(self, mock_get_config_dir):
        """Test ensuring the config directory exists."""
        mock_config_dir = MagicMock(spec=Path)
        mock_get_config_dir.return_value = mock_config_dir

        ensure_config_dir_exists()

        mock_config_dir.mkdir.assert_called_once_with(exist_ok=True)


class TestUILauncher:
    """Test UI launcher functionality."""

    @patch('openhands.cli.ui_launcher.check_docker_requirements')
    def test_launch_ui_server_docker_not_available(self, mock_check_docker):
        """Test UI launcher when Docker is not available."""
        mock_check_docker.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            launch_ui_server()

        assert exc_info.value.code == 1
        mock_check_docker.assert_called_once()

    @patch('openhands.cli.ui_launcher.check_docker_requirements')
    @patch('openhands.cli.ui_launcher.ensure_config_dir_exists')
    @patch('openhands.cli.ui_launcher.get_openhands_config_dir')
    @patch('openhands.cli.ui_launcher.__version__', '0.49.0')
    def test_launch_ui_server_dry_run(
        self, mock_get_config_dir, mock_ensure_config, mock_check_docker
    ):
        """Test UI launcher in dry run mode."""
        mock_check_docker.return_value = True
        mock_config_dir = Path('/test/.openhands')
        mock_get_config_dir.return_value = mock_config_dir

        with patch('openhands.cli.ui_launcher.print_formatted_text') as mock_print:
            launch_ui_server(dry_run=True)

        mock_check_docker.assert_called_once()
        mock_ensure_config.assert_called_once()
        mock_get_config_dir.assert_called_once()
        mock_print.assert_called()

    @patch('openhands.cli.ui_launcher.check_docker_requirements')
    @patch('openhands.cli.ui_launcher.ensure_config_dir_exists')
    @patch('openhands.cli.ui_launcher.get_openhands_config_dir')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    @patch('openhands.cli.ui_launcher.__version__', '0.49.0')
    def test_launch_ui_server_pull_failure(
        self, mock_run, mock_get_config_dir, mock_ensure_config, mock_check_docker
    ):
        """Test UI launcher when Docker pull fails."""
        mock_check_docker.return_value = True
        mock_config_dir = Path('/test/.openhands')
        mock_get_config_dir.return_value = mock_config_dir
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker')

        with pytest.raises(SystemExit) as exc_info:
            with patch('openhands.cli.ui_launcher.print_formatted_text'):
                launch_ui_server()

        assert exc_info.value.code == 1
        mock_run.assert_called_once()

    @patch('openhands.cli.ui_launcher.check_docker_requirements')
    @patch('openhands.cli.ui_launcher.ensure_config_dir_exists')
    @patch('openhands.cli.ui_launcher.get_openhands_config_dir')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    @patch('openhands.cli.ui_launcher.__version__', '0.49.0')
    def test_launch_ui_server_success(
        self, mock_run, mock_get_config_dir, mock_ensure_config, mock_check_docker
    ):
        """Test successful UI launcher execution."""
        mock_check_docker.return_value = True
        mock_config_dir = Path('/test/.openhands')
        mock_get_config_dir.return_value = mock_config_dir

        # Mock successful subprocess calls
        mock_run.return_value = MagicMock(returncode=0)

        with patch('openhands.cli.ui_launcher.print_formatted_text'):
            launch_ui_server()

        # Should be called twice: once for pull, once for run
        assert mock_run.call_count == 2

        # Check the pull command
        pull_call = mock_run.call_args_list[0]
        assert pull_call[0][0] == [
            'docker',
            'pull',
            'docker.all-hands.dev/all-hands-ai/runtime:0.49.0-nikolaik',
        ]

        # Check the run command
        run_call = mock_run.call_args_list[1]
        expected_cmd = [
            'docker',
            'run',
            '-it',
            '--rm',
            '--pull=always',
            '-e',
            'SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.49.0-nikolaik',
            '-e',
            'LOG_ALL_EVENTS=true',
            '-v',
            '/var/run/docker.sock:/var/run/docker.sock',
            '-v',
            f'{mock_config_dir}:/.openhands',
            '-p',
            '3000:3000',
            '--add-host',
            'host.docker.internal:host-gateway',
            '--name',
            'openhands-app',
            'docker.all-hands.dev/all-hands-ai/openhands:0.49.0',
        ]
        assert run_call[0][0] == expected_cmd

    @patch('openhands.cli.ui_launcher.check_docker_requirements')
    @patch('openhands.cli.ui_launcher.ensure_config_dir_exists')
    @patch('openhands.cli.ui_launcher.get_openhands_config_dir')
    @patch('openhands.cli.ui_launcher.subprocess.run')
    @patch('openhands.cli.ui_launcher.__version__', '0.49.0')
    def test_launch_ui_server_keyboard_interrupt(
        self, mock_run, mock_get_config_dir, mock_ensure_config, mock_check_docker
    ):
        """Test UI launcher handling of keyboard interrupt."""
        mock_check_docker.return_value = True
        mock_config_dir = Path('/test/.openhands')
        mock_get_config_dir.return_value = mock_config_dir

        # Mock successful pull, then KeyboardInterrupt on run
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Successful pull
            KeyboardInterrupt(),  # Interrupted run
        ]

        with pytest.raises(SystemExit) as exc_info:
            with patch('openhands.cli.ui_launcher.print_formatted_text'):
                launch_ui_server()

        assert exc_info.value.code == 0  # Should exit gracefully
        assert mock_run.call_count == 2
