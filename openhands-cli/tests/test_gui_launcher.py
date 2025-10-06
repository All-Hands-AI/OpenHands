"""Tests for GUI launcher functionality."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openhands_cli.gui_launcher import (
    _format_docker_command_for_logging,
    check_docker_requirements,
    ensure_config_dir_exists,
    get_openhands_version,
    launch_gui_server,
)


class TestFormatDockerCommand:
    """Test the Docker command formatting function."""

    def test_format_docker_command_simple(self):
        """Test formatting a simple Docker command."""
        cmd = ['docker', 'run', 'hello-world']
        result = _format_docker_command_for_logging(cmd)
        expected = '<grey>Running Docker command: docker run hello-world</grey>'
        assert result == expected

    def test_format_docker_command_complex(self):
        """Test formatting a complex Docker command with many arguments."""
        cmd = [
            'docker',
            'run',
            '-it',
            '--rm',
            '-p',
            '3000:3000',
            'openhands:latest',
        ]
        result = _format_docker_command_for_logging(cmd)
        expected = '<grey>Running Docker command: docker run -it --rm -p 3000:3000 openhands:latest</grey>'
        assert result == expected

    def test_format_docker_command_empty(self):
        """Test formatting an empty command list."""
        cmd = []
        result = _format_docker_command_for_logging(cmd)
        expected = '<grey>Running Docker command: </grey>'
        assert result == expected


class TestCheckDockerRequirements:
    """Test Docker requirements checking."""

    @patch('shutil.which')
    def test_docker_not_installed(self, mock_which):
        """Test when Docker is not installed."""
        mock_which.return_value = None
        
        with patch('openhands_cli.gui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()
            
        assert result is False
        assert mock_print.call_count == 2  # Two print statements

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_docker_daemon_not_running(self, mock_run, mock_which):
        """Test when Docker is installed but daemon is not running."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.return_value = MagicMock(returncode=1)
        
        with patch('openhands_cli.gui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()
            
        assert result is False
        assert mock_print.call_count == 2  # Two print statements

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_docker_timeout(self, mock_run, mock_which):
        """Test when Docker info command times out."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.side_effect = subprocess.TimeoutExpired('docker info', 10)
        
        with patch('openhands_cli.gui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()
            
        assert result is False
        assert mock_print.call_count == 2  # Two print statements

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_docker_available(self, mock_run, mock_which):
        """Test when Docker is available and running."""
        mock_which.return_value = '/usr/bin/docker'
        mock_run.return_value = MagicMock(returncode=0)
        
        result = check_docker_requirements()
        
        assert result is True


class TestEnsureConfigDirExists:
    """Test configuration directory creation."""

    @patch('pathlib.Path.home')
    def test_config_dir_creation(self, mock_home):
        """Test that config directory is created if it doesn't exist."""
        mock_home_path = MagicMock()
        mock_home.return_value = mock_home_path
        mock_config_dir = MagicMock()
        mock_home_path.__truediv__.return_value = mock_config_dir
        
        result = ensure_config_dir_exists()
        
        mock_home_path.__truediv__.assert_called_once_with('.openhands')
        mock_config_dir.mkdir.assert_called_once_with(exist_ok=True)
        assert result == mock_config_dir


class TestGetOpenHandsVersion:
    """Test version retrieval."""

    def test_default_version(self):
        """Test default version when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_openhands_version()
            assert result == 'latest'

    def test_environment_version(self):
        """Test version from environment variable."""
        with patch.dict(os.environ, {'OPENHANDS_VERSION': '1.2.3'}):
            result = get_openhands_version()
            assert result == '1.2.3'


class TestLaunchGuiServer:
    """Test GUI server launching."""

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    def test_launch_gui_server_docker_not_available(self, mock_check_docker):
        """Test that launch_gui_server exits when Docker is not available."""
        mock_check_docker.return_value = False
        
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.gui_launcher.print_formatted_text'):
                launch_gui_server()
        
        mock_exit.assert_called_once_with(1)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    def test_launch_gui_server_pull_failure(
        self, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test that launch_gui_server exits when Docker pull fails."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker pull')
        
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.gui_launcher.print_formatted_text'):
                launch_gui_server()
        
        mock_exit.assert_called_once_with(1)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    def test_launch_gui_server_pull_timeout(
        self, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test that launch_gui_server exits when Docker pull times out."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        mock_run.side_effect = subprocess.TimeoutExpired('docker pull', 300)
        
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.gui_launcher.print_formatted_text'):
                launch_gui_server()
        
        mock_exit.assert_called_once_with(1)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_launch_gui_server_success_with_mount_cwd(
        self, mock_check_output, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test successful GUI server launch with current directory mounting."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        mock_check_output.return_value = '1000\n'
        
        # Mock successful pull and run
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Successful pull
            MagicMock(returncode=0),  # Successful run
        ]
        
        with patch('openhands_cli.gui_launcher.print_formatted_text'):
            with patch('pathlib.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path('/current/dir')
                launch_gui_server(mount_cwd=True)
        
        # Verify that docker run was called with the correct arguments
        assert mock_run.call_count == 2
        run_call = mock_run.call_args_list[1]
        docker_cmd = run_call[0][0]
        
        # Check that the command includes mount options
        assert 'SANDBOX_VOLUMES=/current/dir:/workspace:rw' in ' '.join(docker_cmd)
        assert 'SANDBOX_USER_ID=1000' in ' '.join(docker_cmd)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    def test_launch_gui_server_success_with_gpu(
        self, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test successful GUI server launch with GPU support."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        
        # Mock successful pull and run
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Successful pull
            MagicMock(returncode=0),  # Successful run
        ]
        
        with patch('openhands_cli.gui_launcher.print_formatted_text'):
            launch_gui_server(gpu=True)
        
        # Verify that docker run was called with GPU options
        assert mock_run.call_count == 2
        run_call = mock_run.call_args_list[1]
        docker_cmd = run_call[0][0]
        
        # Check that the command includes GPU options
        assert '--gpus' in docker_cmd
        assert 'all' in docker_cmd
        assert 'SANDBOX_ENABLE_GPU=true' in ' '.join(docker_cmd)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    def test_launch_gui_server_keyboard_interrupt(
        self, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test that KeyboardInterrupt is handled gracefully."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        
        # Mock successful pull, then KeyboardInterrupt on run
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Successful pull
            KeyboardInterrupt(),     # User interruption
        ]
        
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.gui_launcher.print_formatted_text'):
                launch_gui_server()
        
        mock_exit.assert_called_once_with(0)

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    def test_launch_gui_server_run_failure(
        self, mock_run, mock_version, mock_config_dir, mock_check_docker
    ):
        """Test that launch_gui_server exits when Docker run fails."""
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        
        # Mock successful pull, then failure on run
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Successful pull
            subprocess.CalledProcessError(1, 'docker run'),  # Failed run
        ]
        
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.gui_launcher.print_formatted_text'):
                launch_gui_server()
        
        mock_exit.assert_called_once_with(1)