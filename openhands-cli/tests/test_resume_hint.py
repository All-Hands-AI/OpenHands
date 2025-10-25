#!/usr/bin/env python3
"""Tests for resume command hint functionality."""

import sys
from unittest.mock import patch

import pytest

from openhands_cli.agent_chat import _get_current_command


class TestResumeHint:
    """Test cases for resume command hint generation."""

    def test_get_current_command_with_relative_path(self):
        """Test command detection with relative path (./)."""
        with patch.object(sys, 'argv', ['./openhands-cli']):
            result = _get_current_command()
            assert result == './openhands-cli'

    def test_get_current_command_with_absolute_path(self):
        """Test command detection with absolute path."""
        with patch.object(sys, 'argv', ['/usr/local/bin/openhands']):
            result = _get_current_command()
            assert result == 'openhands'

    def test_get_current_command_with_python_script(self):
        """Test command detection when running as Python script."""
        with patch.object(sys, 'argv', ['openhands_cli/simple_main.py']):
            result = _get_current_command()
            assert result == 'openhands'

    def test_get_current_command_with_renamed_binary(self):
        """Test command detection with renamed binary."""
        with patch.object(sys, 'argv', ['my-custom-openhands']):
            result = _get_current_command()
            assert result == 'my-custom-openhands'

    def test_get_current_command_with_relative_renamed_binary(self):
        """Test command detection with relative path to renamed binary."""
        with patch.object(sys, 'argv', ['./my-custom-openhands']):
            result = _get_current_command()
            assert result == './my-custom-openhands'

    def test_get_current_command_fallback(self):
        """Test fallback when sys.argv is empty."""
        with patch.object(sys, 'argv', []):
            result = _get_current_command()
            assert result == 'openhands'

    def test_get_current_command_with_uv_run(self):
        """Test command detection when using uv run."""
        # This simulates: uv run openhands
        with patch.object(sys, 'argv', ['openhands']):
            result = _get_current_command()
            assert result == 'openhands'

    def test_get_current_command_windows_path(self):
        """Test command detection with Windows-style path."""
        with patch.object(sys, 'argv', ['C:\\Users\\user\\openhands.exe']):
            result = _get_current_command()
            assert result == 'openhands.exe'

    def test_get_current_command_with_path_containing_spaces(self):
        """Test command detection with path containing spaces."""
        with patch.object(sys, 'argv', ['/path with spaces/openhands']):
            result = _get_current_command()
            assert result == 'openhands'


if __name__ == '__main__':
    pytest.main([__file__])