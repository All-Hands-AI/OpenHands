"""Unit tests for CLI alias setup functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from openhands.cli.utils import (
    add_aliases_to_bash_profile,
    get_bash_profile_path,
    has_alias_setup_been_completed,
    is_first_time_user,
    mark_alias_setup_completed,
)


class TestAliasSetup:
    """Test cases for alias setup functionality."""

    def test_is_first_time_user_no_config_dir(self):
        """Test first time user detection when .openhands doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                assert is_first_time_user() is True

    def test_is_first_time_user_with_config_dir(self):
        """Test first time user detection when .openhands exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create .openhands directory
                openhands_dir = Path(temp_dir) / '.openhands'
                openhands_dir.mkdir()

                assert is_first_time_user() is False

    def test_alias_setup_completion_tracking(self):
        """Test alias setup completion tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Should not be completed initially
                assert has_alias_setup_been_completed() is False

                # Mark as completed
                mark_alias_setup_completed()

                # Should be completed now
                assert has_alias_setup_been_completed() is True

    def test_get_bash_profile_path_no_files(self):
        """Test bash profile path when neither .bashrc nor .bash_profile exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                profile_path = get_bash_profile_path()
                assert profile_path.name == '.bash_profile'

    def test_get_bash_profile_path_prefers_bashrc(self):
        """Test bash profile path prefers .bashrc when it exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create .bashrc
                bashrc = Path(temp_dir) / '.bashrc'
                bashrc.touch()

                profile_path = get_bash_profile_path()
                assert profile_path.name == '.bashrc'

    def test_add_aliases_to_bash_profile(self):
        """Test adding aliases to bash profile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Add aliases
                success = add_aliases_to_bash_profile()
                assert success is True

                # Check that the aliases were added
                profile_path = get_bash_profile_path()
                with open(profile_path, 'r') as f:
                    content = f.read()
                    assert 'alias openhands=' in content
                    assert 'alias oh=' in content
                    assert 'uvx --python 3.12 --from openhands-ai openhands' in content

    def test_add_aliases_handles_existing_aliases(self):
        """Test that adding aliases handles existing aliases correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Add aliases first time
                success = add_aliases_to_bash_profile()
                assert success is True

                # Try adding again - should detect existing aliases
                success = add_aliases_to_bash_profile()
                assert success is True

                # Check that aliases weren't duplicated
                profile_path = get_bash_profile_path()
                with open(profile_path, 'r') as f:
                    content = f.read()
                    # Count occurrences of the alias
                    openhands_count = content.count('alias openhands=')
                    oh_count = content.count('alias oh=')
                    assert openhands_count == 1
                    assert oh_count == 1

    def test_mark_alias_setup_completed_creates_directory(self):
        """Test that marking alias setup completed creates the .openhands directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Directory shouldn't exist initially
                openhands_dir = Path(temp_dir) / '.openhands'
                assert not openhands_dir.exists()

                # Mark as completed
                mark_alias_setup_completed()

                # Directory should exist now
                assert openhands_dir.exists()
                assert openhands_dir.is_dir()

                # Marker file should exist
                marker_file = openhands_dir / '.alias_setup_completed'
                assert marker_file.exists()
