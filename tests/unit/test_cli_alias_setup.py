"""Unit tests for CLI alias setup functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from openhands.cli.utils import (
    add_aliases_to_shell_config,
    get_shell_config_path,
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

    def test_get_shell_config_path_no_files_fallback(self):
        """Test shell config path fallback when no shell detection and no config files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Mock shellingham to raise an exception (detection failure)
                with patch(
                    'shellingham.detect_shell',
                    side_effect=Exception('Shell detection failed'),
                ):
                    profile_path = get_shell_config_path()
                    assert profile_path.name == '.bash_profile'

    def test_get_shell_config_path_bash_fallback(self):
        """Test shell config path fallback to bash when it exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create .bashrc
                bashrc = Path(temp_dir) / '.bashrc'
                bashrc.touch()

                # Mock shellingham to raise an exception (detection failure)
                with patch(
                    'shellingham.detect_shell',
                    side_effect=Exception('Shell detection failed'),
                ):
                    profile_path = get_shell_config_path()
                    assert profile_path.name == '.bashrc'

    def test_get_shell_config_path_with_bash_detection(self):
        """Test shell config path when bash is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create .bashrc
                bashrc = Path(temp_dir) / '.bashrc'
                bashrc.touch()

                # Mock shellingham to return bash
                with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                    profile_path = get_shell_config_path()
                    assert profile_path.name == '.bashrc'

    def test_get_shell_config_path_with_zsh_detection(self):
        """Test shell config path when zsh is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create .zshrc
                zshrc = Path(temp_dir) / '.zshrc'
                zshrc.touch()

                # Mock shellingham to return zsh
                with patch('shellingham.detect_shell', return_value=('zsh', 'zsh')):
                    profile_path = get_shell_config_path()
                    assert profile_path.name == '.zshrc'

    def test_get_shell_config_path_with_fish_detection(self):
        """Test shell config path when fish is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Create fish config directory and file
                fish_config_dir = Path(temp_dir) / '.config' / 'fish'
                fish_config_dir.mkdir(parents=True)
                fish_config = fish_config_dir / 'config.fish'
                fish_config.touch()

                # Mock shellingham to return fish
                with patch('shellingham.detect_shell', return_value=('fish', 'fish')):
                    profile_path = get_shell_config_path()
                    assert profile_path.name == 'config.fish'
                    assert 'fish' in str(profile_path)

    def test_add_aliases_to_shell_config_bash(self):
        """Test adding aliases to bash config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Mock shellingham to return bash
                with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                    # Add aliases
                    success = add_aliases_to_shell_config()
                    assert success is True

                    # Get the actual path that was used
                    with patch(
                        'shellingham.detect_shell', return_value=('bash', 'bash')
                    ):
                        profile_path = get_shell_config_path()

                    # Check that the aliases were added
                    with open(profile_path, 'r') as f:
                        content = f.read()
                        assert 'alias openhands=' in content
                        assert 'alias oh=' in content
                        assert (
                            'uvx --python 3.12 --from openhands-ai openhands' in content
                        )

    def test_add_aliases_to_shell_config_zsh(self):
        """Test adding aliases to zsh config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Mock shellingham to return zsh
                with patch('shellingham.detect_shell', return_value=('zsh', 'zsh')):
                    # Add aliases
                    success = add_aliases_to_shell_config()
                    assert success is True

                    # Check that the aliases were added to .zshrc
                    profile_path = Path(temp_dir) / '.zshrc'
                    with open(profile_path, 'r') as f:
                        content = f.read()
                        assert 'alias openhands=' in content
                        assert 'alias oh=' in content
                        assert (
                            'uvx --python 3.12 --from openhands-ai openhands' in content
                        )

    def test_add_aliases_handles_existing_aliases(self):
        """Test that adding aliases handles existing aliases correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.cli.utils.Path.home', return_value=Path(temp_dir)):
                # Mock shellingham to return bash
                with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                    # Add aliases first time
                    success = add_aliases_to_shell_config()
                    assert success is True

                    # Try adding again - should detect existing aliases
                    success = add_aliases_to_shell_config()
                    assert success is True

                    # Get the actual path that was used
                    with patch(
                        'shellingham.detect_shell', return_value=('bash', 'bash')
                    ):
                        profile_path = get_shell_config_path()

                    # Check that aliases weren't duplicated
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
