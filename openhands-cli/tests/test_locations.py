#!/usr/bin/env python3
"""
Tests for locations module in OpenHands CLI.
"""

import os
from unittest.mock import patch

import pytest

from openhands_cli.locations import LLM_SETTINGS_PATH


class TestLocations:
    """Test suite for locations module."""

    def test_llm_settings_path_expansion(self) -> None:
        """Test that LLM_SETTINGS_PATH correctly expands user home directory."""
        # The path should be expanded and contain the expected structure
        assert LLM_SETTINGS_PATH.endswith("/.openhands/llm_settings.json")
        assert "~" not in LLM_SETTINGS_PATH  # Should be expanded

    @patch("os.path.expanduser")
    def test_llm_settings_path_uses_expanduser(self, mock_expanduser: any) -> None:
        """Test that LLM_SETTINGS_PATH uses os.path.expanduser."""
        mock_expanduser.return_value = "/mocked/home/.openhands/llm_settings.json"
        
        # Re-import to trigger the expanduser call
        import importlib
        from openhands_cli import locations
        importlib.reload(locations)
        
        # Verify expanduser was called with the expected path
        mock_expanduser.assert_called_with("~/.openhands/llm_settings.json")
        assert locations.LLM_SETTINGS_PATH == "/mocked/home/.openhands/llm_settings.json"

    def test_llm_settings_path_is_absolute(self) -> None:
        """Test that LLM_SETTINGS_PATH is an absolute path."""
        assert os.path.isabs(LLM_SETTINGS_PATH)

    def test_llm_settings_path_structure(self) -> None:
        """Test that LLM_SETTINGS_PATH has the correct directory structure."""
        # Should end with .openhands/llm_settings.json
        path_parts = LLM_SETTINGS_PATH.split(os.sep)
        assert path_parts[-2] == ".openhands"
        assert path_parts[-1] == "llm_settings.json"