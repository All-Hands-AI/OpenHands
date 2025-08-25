"""Test the serve command and its options."""

import argparse
from unittest.mock import MagicMock, patch

from openhands.core.config.arg_utils import get_cli_parser


class TestServeCommand:
    """Test the serve command functionality."""

    def test_serve_command_has_port_option(self):
        """Test that the serve command includes a port option."""
        parser = get_cli_parser()

        # Parse serve command with port
        args = parser.parse_args(['serve', '--port', '4242'])

        assert args.command == 'serve'
        assert args.port == 4242
        assert args.mount_cwd is False
        assert args.gpu is False

    def test_serve_command_default_port(self):
        """Test that the serve command has a default port of 3000."""
        parser = get_cli_parser()

        # Parse serve command without port
        args = parser.parse_args(['serve'])

        assert args.command == 'serve'
        assert args.port == 3000

    def test_serve_command_with_all_options(self):
        """Test that all serve command options work together."""
        parser = get_cli_parser()

        # Parse serve command with all options
        args = parser.parse_args(['serve', '--mount-cwd', '--gpu', '--port', '8080'])

        assert args.command == 'serve'
        assert args.mount_cwd is True
        assert args.gpu is True
        assert args.port == 8080

    @patch('openhands.cli.gui_launcher.check_docker_requirements')
    @patch('openhands.cli.gui_launcher.subprocess.run')
    def test_launch_gui_server_with_custom_port(self, mock_run, mock_check_docker):
        """Test that launch_gui_server uses the custom port correctly."""
        from openhands.cli.gui_launcher import launch_gui_server

        # Mock Docker check to return True
        mock_check_docker.return_value = True

        # Mock subprocess.run to avoid actually running Docker
        mock_run.return_value = MagicMock(returncode=0)

        # Call launch_gui_server with custom port
        try:
            launch_gui_server(port=4242)
        except KeyboardInterrupt:
            # Expected since we're mocking the subprocess
            pass

        # Check that Docker was called with the correct port mapping
        mock_run.assert_called()
        docker_cmd = mock_run.call_args[0][0]

        # Find the port mapping in the command
        port_index = docker_cmd.index('-p') + 1
        assert docker_cmd[port_index] == '4242:3000'

    def test_serve_help_includes_port(self):
        """Test that the serve command help includes port information."""
        parser = get_cli_parser()

        # Get the serve subparser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert len(subparsers_actions) == 1
        serve_parser = subparsers_actions[0].choices['serve']

        # Check that port argument exists
        port_actions = [
            action for action in serve_parser._actions if action.dest == 'port'
        ]

        assert len(port_actions) == 1
        port_action = port_actions[0]

        assert port_action.type is int
        assert port_action.default == 3000
        assert 'Port to run the OpenHands GUI server on' in port_action.help
