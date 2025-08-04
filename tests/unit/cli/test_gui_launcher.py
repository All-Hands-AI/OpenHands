"""Tests for the GUI launcher module."""

import pytest
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands.cli.gui_launcher import _format_docker_command_for_logging


class TestGuiLauncher:
    """Test cases for GUI launcher functionality."""

    def test_format_docker_command_for_logging_returns_valid_html(self):
        """Test that _format_docker_command_for_logging returns valid HTML."""
        # Test with a typical Docker command
        cmd = [
            'docker',
            'pull',
            'docker.all-hands.dev/all-hands-ai/runtime:0.51.1-nikolaik',
        ]

        result = _format_docker_command_for_logging(cmd)

        # Should return HTML-formatted string
        expected = '<grey>Running Docker command: docker pull docker.all-hands.dev/all-hands-ai/runtime:0.51.1-nikolaik</grey>'
        assert result == expected

        # Should be parseable as HTML without raising an exception
        try:
            print_formatted_text(HTML(result))
        except Exception as e:
            pytest.fail(f'HTML parsing failed: {e}')

    def test_format_docker_command_for_logging_with_complex_command(self):
        """Test formatting with a complex Docker command containing special characters."""
        # Test with a complex command that might contain characters that could break XML parsing
        cmd = [
            'docker',
            'run',
            '-it',
            '--rm',
            '-e',
            'SANDBOX_RUNTIME_CONTAINER_IMAGE=test:latest',
            '-v',
            '/var/run/docker.sock:/var/run/docker.sock',
            'test-image',
        ]

        result = _format_docker_command_for_logging(cmd)

        # Should contain the full command
        assert (
            'docker run -it --rm -e SANDBOX_RUNTIME_CONTAINER_IMAGE=test:latest -v /var/run/docker.sock:/var/run/docker.sock test-image'
            in result
        )

        # Should be wrapped in grey tags
        assert result.startswith('<grey>')
        assert result.endswith('</grey>')

        # Should be parseable as HTML
        try:
            print_formatted_text(HTML(result))
        except Exception as e:
            pytest.fail(f'HTML parsing failed: {e}')

    def test_format_docker_command_for_logging_empty_command(self):
        """Test formatting with an empty command list."""
        cmd = []

        result = _format_docker_command_for_logging(cmd)

        expected = '<grey>Running Docker command: </grey>'
        assert result == expected

        # Should be parseable as HTML
        try:
            print_formatted_text(HTML(result))
        except Exception as e:
            pytest.fail(f'HTML parsing failed: {e}')

    def test_format_docker_command_for_logging_single_command(self):
        """Test formatting with a single command."""
        cmd = ['docker']

        result = _format_docker_command_for_logging(cmd)

        expected = '<grey>Running Docker command: docker</grey>'
        assert result == expected

        # Should be parseable as HTML
        try:
            print_formatted_text(HTML(result))
        except Exception as e:
            pytest.fail(f'HTML parsing failed: {e}')
