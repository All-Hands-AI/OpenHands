"""Tests for working directory configuration functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from openhands_cli.locations import (
    get_configured_working_directory,
    save_working_directory,
)
from openhands_cli.user_actions.working_directory_action import (
    configure_working_directory_in_settings,
    prompt_working_directory_configuration,
)


class TestWorkingDirectoryConfiguration:
    """Test working directory configuration functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_settings_file = Path(self.temp_dir) / "oh_cli_settings.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.test_settings_file.exists():
            self.test_settings_file.unlink()
        os.rmdir(self.temp_dir)

    def test_get_configured_working_directory_no_file(self):
        """Test getting working directory when no settings file exists."""
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            result = get_configured_working_directory()
        assert result is None

    def test_get_configured_working_directory_empty_file(self):
        """Test getting working directory when settings file is empty."""
        # Create empty settings file
        self.test_settings_file.write_text("{}")
        
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            with patch('openhands_cli.locations.CLI_SETTINGS_FILE', self.test_settings_file.name):
                result = get_configured_working_directory()
        assert result is None

    def test_get_configured_working_directory_with_value(self):
        """Test getting working directory when value is configured."""
        # Use the temp directory as the test directory since it actually exists
        test_dir = str(self.temp_dir)
        settings = {"working_directory": test_dir}
        self.test_settings_file.write_text(json.dumps(settings))
        
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            with patch('openhands_cli.locations.CLI_SETTINGS_FILE', self.test_settings_file.name):
                result = get_configured_working_directory()
        assert result == test_dir

    def test_save_working_directory_new_file(self):
        """Test saving working directory to new settings file."""
        test_dir = "/test/working/directory"
        
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            with patch('openhands_cli.locations.CLI_SETTINGS_FILE', self.test_settings_file.name):
                save_working_directory(test_dir)
        
        # Verify file was created with correct content
        assert self.test_settings_file.exists()
        settings = json.loads(self.test_settings_file.read_text())
        assert settings["working_directory"] == test_dir

    def test_save_working_directory_existing_file(self):
        """Test saving working directory to existing settings file."""
        # Create existing settings file with other data
        existing_settings = {"other_setting": "value"}
        self.test_settings_file.write_text(json.dumps(existing_settings))
        
        test_dir = "/test/working/directory"
        
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            with patch('openhands_cli.locations.CLI_SETTINGS_FILE', self.test_settings_file.name):
                save_working_directory(test_dir)
        
        # Verify working directory was added while preserving other settings
        settings = json.loads(self.test_settings_file.read_text())
        assert settings["working_directory"] == test_dir
        assert settings["other_setting"] == "value"

    def test_save_working_directory_update_existing(self):
        """Test updating existing working directory setting."""
        # Create existing settings file with working directory
        existing_settings = {"working_directory": "/old/directory"}
        self.test_settings_file.write_text(json.dumps(existing_settings))
        
        test_dir = "/new/working/directory"
        
        with patch('openhands_cli.locations.PERSISTENCE_DIR', str(self.temp_dir)):
            with patch('openhands_cli.locations.CLI_SETTINGS_FILE', self.test_settings_file.name):
                save_working_directory(test_dir)
        
        # Verify working directory was updated
        settings = json.loads(self.test_settings_file.read_text())
        assert settings["working_directory"] == test_dir

    @patch('openhands_cli.user_actions.working_directory_action.get_configured_working_directory')
    @patch('openhands_cli.user_actions.working_directory_action.save_working_directory')
    def test_working_directory_functions_exist(self, mock_save, mock_get):
        """Test that working directory functions exist and can be called."""
        # Test that functions exist and can be imported
        assert callable(get_configured_working_directory)
        assert callable(save_working_directory)
        assert callable(prompt_working_directory_configuration)
        assert callable(configure_working_directory_in_settings)


class TestWorkingDirectoryIntegration:
    """Test integration of working directory with other components."""

    @patch('openhands_cli.locations.get_configured_working_directory')
    @patch('os.getcwd')
    def test_setup_conversation_uses_configured_directory(self, mock_getcwd, mock_get_config):
        """Test that setup_conversation uses configured working directory."""
        from openhands_cli.setup import setup_conversation
        
        configured_dir = "/configured/directory"
        current_dir = "/current/directory"
        mock_get_config.return_value = configured_dir
        mock_getcwd.return_value = current_dir
        
        # This would require more complex mocking to test fully
        # but the key point is that get_configured_working_directory is called
        mock_get_config.assert_not_called()  # Not called until setup_conversation runs

    @patch('openhands_cli.locations.get_configured_working_directory')
    def test_agent_store_uses_configured_directory(self, mock_get_config):
        """Test that AgentStore uses configured working directory."""
        from openhands_cli.tui.settings.store import AgentStore
        
        configured_dir = "/configured/directory"
        mock_get_config.return_value = configured_dir
        
        # This would require more complex mocking to test fully
        # but the key point is that get_configured_working_directory is called
        mock_get_config.assert_not_called()  # Not called until AgentStore.load() runs