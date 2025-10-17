"""Tests for GUI launcher functionality."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openhands_cli.gui_launcher import (
    _format_docker_command_for_logging,
    check_docker_requirements,
    get_openhands_version,
    launch_gui_server,
)


class TestFormatDockerCommand:
    """Test the Docker command formatting function."""

    @pytest.mark.parametrize(
        "cmd,expected",
        [
            (
                ['docker', 'run', 'hello-world'],
                '<grey>Running Docker command: docker run hello-world</grey>',
            ),
            (
                ['docker', 'run', '-it', '--rm', '-p', '3000:3000', 'openhands:latest'],
                '<grey>Running Docker command: docker run -it --rm -p 3000:3000 openhands:latest</grey>',
            ),
            ([], '<grey>Running Docker command: </grey>'),
        ],
    )
    def test_format_docker_command(self, cmd, expected):
        """Test formatting Docker commands."""
        result = _format_docker_command_for_logging(cmd)
        assert result == expected


class TestCheckDockerRequirements:
    """Test Docker requirements checking."""

    @pytest.mark.parametrize(
        "which_return,run_side_effect,expected_result,expected_print_count",
        [
            # Docker not installed
            (None, None, False, 2),
            # Docker daemon not running
            ('/usr/bin/docker', MagicMock(returncode=1), False, 2),
            # Docker timeout
            ('/usr/bin/docker', subprocess.TimeoutExpired('docker info', 10), False, 2),
            # Docker available
            ('/usr/bin/docker', MagicMock(returncode=0), True, 0),
        ],
    )
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_docker_requirements(
        self, mock_run, mock_which, which_return, run_side_effect, expected_result, expected_print_count
    ):
        """Test Docker requirements checking scenarios."""
        mock_which.return_value = which_return
        if run_side_effect is not None:
            if isinstance(run_side_effect, Exception):
                mock_run.side_effect = run_side_effect
            else:
                mock_run.return_value = run_side_effect

        with patch('openhands_cli.gui_launcher.print_formatted_text') as mock_print:
            result = check_docker_requirements()

        assert result is expected_result
        assert mock_print.call_count == expected_print_count


class TestGetOpenHandsVersion:
    """Test version retrieval."""

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            (None, 'latest'),  # No environment variable set
            ('1.2.3', '1.2.3'),  # Environment variable set
        ],
    )
    def test_version_retrieval(self, env_value, expected):
        """Test version retrieval from environment."""
        if env_value:
            os.environ['OPENHANDS_VERSION'] = env_value
        result = get_openhands_version()
        assert result == expected


class TestLaunchGuiServer:
    """Test GUI server launching."""

    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.print_formatted_text')
    def test_launch_gui_server_docker_not_available(self, mock_print, mock_check_docker):
        """Test that launch_gui_server exits when Docker is not available."""
        mock_check_docker.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            launch_gui_server()

        assert exc_info.value.code == 1

    @pytest.mark.parametrize(
        "pull_side_effect,run_side_effect,expected_exit_code,mount_cwd,gpu",
        [
            # Docker pull failure
            (subprocess.CalledProcessError(1, 'docker pull'), None, 1, False, False),
            # Docker run failure
            (MagicMock(returncode=0), subprocess.CalledProcessError(1, 'docker run'), 1, False, False),
            # KeyboardInterrupt during run
            (MagicMock(returncode=0), KeyboardInterrupt(), 0, False, False),
            # Success with mount_cwd
            (MagicMock(returncode=0), MagicMock(returncode=0), None, True, False),
            # Success with GPU
            (MagicMock(returncode=0), MagicMock(returncode=0), None, False, True),
        ],
    )
    @patch('openhands_cli.gui_launcher.check_docker_requirements')
    @patch('openhands_cli.gui_launcher.ensure_config_dir_exists')
    @patch('openhands_cli.gui_launcher.get_openhands_version')
    @patch('subprocess.run')
    @patch('subprocess.check_output')
    @patch('pathlib.Path.cwd')
    @patch('openhands_cli.gui_launcher.print_formatted_text')
    def test_launch_gui_server_scenarios(
        self,
        mock_print,
        mock_cwd,
        mock_check_output,
        mock_run,
        mock_version,
        mock_config_dir,
        mock_check_docker,
        pull_side_effect,
        run_side_effect,
        expected_exit_code,
        mount_cwd,
        gpu,
    ):
        """Test various GUI server launch scenarios."""
        # Setup mocks
        mock_check_docker.return_value = True
        mock_config_dir.return_value = Path('/home/user/.openhands')
        mock_version.return_value = 'latest'
        mock_check_output.return_value = '1000\n'
        mock_cwd.return_value = Path('/current/dir')

        # Configure subprocess.run side effects
        side_effects = []
        if pull_side_effect is not None:
            if isinstance(pull_side_effect, Exception):
                side_effects.append(pull_side_effect)
            else:
                side_effects.append(pull_side_effect)

        if run_side_effect is not None:
            if isinstance(run_side_effect, Exception):
                side_effects.append(run_side_effect)
            else:
                side_effects.append(run_side_effect)

        mock_run.side_effect = side_effects

        # Test the function
        if expected_exit_code is not None:
            with pytest.raises(SystemExit) as exc_info:
                launch_gui_server(mount_cwd=mount_cwd, gpu=gpu)
            assert exc_info.value.code == expected_exit_code
        else:
            # Should not raise SystemExit for successful cases
            launch_gui_server(mount_cwd=mount_cwd, gpu=gpu)

            # Verify subprocess.run was called correctly
            assert mock_run.call_count == 2  # Pull and run commands

            # Check pull command
            pull_call = mock_run.call_args_list[0]
            pull_cmd = pull_call[0][0]
            assert pull_cmd[0:3] == ['docker', 'pull', 'docker.all-hands.dev/openhands/runtime:latest-nikolaik']

            # Check run command
            run_call = mock_run.call_args_list[1]
            run_cmd = run_call[0][0]
            assert run_cmd[0:2] == ['docker', 'run']

            if mount_cwd:
                assert 'SANDBOX_VOLUMES=/current/dir:/workspace:rw' in ' '.join(run_cmd)
                assert 'SANDBOX_USER_ID=1000' in ' '.join(run_cmd)

            if gpu:
                assert '--gpus' in run_cmd
                assert 'all' in run_cmd
                assert 'SANDBOX_ENABLE_GPU=true' in ' '.join(run_cmd)
