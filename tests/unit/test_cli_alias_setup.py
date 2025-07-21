"""Unit tests for CLI alias setup functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from openhands.cli.main import alias_setup_declined as main_alias_setup_declined
from openhands.cli.main import aliases_exist_in_shell_config, run_alias_setup_flow
from openhands.cli.shell_config import (
    ShellConfigManager,
    add_aliases_to_shell_config,
    alias_setup_declined,
    get_shell_config_path,
    mark_alias_setup_declined,
)
from openhands.core.config import OpenHandsConfig


def test_get_shell_config_path_no_files_fallback():
    """Test shell config path fallback when no shell detection and no config files exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to raise an exception (detection failure)
            with patch(
                'shellingham.detect_shell',
                side_effect=Exception('Shell detection failed'),
            ):
                profile_path = get_shell_config_path()
                assert profile_path.name == '.bash_profile'


def test_get_shell_config_path_bash_fallback():
    """Test shell config path fallback to bash when it exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
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


def test_get_shell_config_path_with_bash_detection():
    """Test shell config path when bash is detected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Create .bashrc
            bashrc = Path(temp_dir) / '.bashrc'
            bashrc.touch()

            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                profile_path = get_shell_config_path()
                assert profile_path.name == '.bashrc'


def test_get_shell_config_path_with_zsh_detection():
    """Test shell config path when zsh is detected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Create .zshrc
            zshrc = Path(temp_dir) / '.zshrc'
            zshrc.touch()

            # Mock shellingham to return zsh
            with patch('shellingham.detect_shell', return_value=('zsh', 'zsh')):
                profile_path = get_shell_config_path()
                assert profile_path.name == '.zshrc'


def test_get_shell_config_path_with_fish_detection():
    """Test shell config path when fish is detected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
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


def test_add_aliases_to_shell_config_bash():
    """Test adding aliases to bash config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                # Add aliases
                success = add_aliases_to_shell_config()
                assert success is True

                # Get the actual path that was used
                with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                    profile_path = get_shell_config_path()

                # Check that the aliases were added
                with open(profile_path, 'r') as f:
                    content = f.read()
                    assert 'alias openhands=' in content
                    assert 'alias oh=' in content
                    assert 'uvx --python 3.12 --from openhands-ai openhands' in content


def test_add_aliases_to_shell_config_zsh():
    """Test adding aliases to zsh config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
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
                    assert 'uvx --python 3.12 --from openhands-ai openhands' in content


def test_add_aliases_handles_existing_aliases():
    """Test that adding aliases handles existing aliases correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                # Add aliases first time
                success = add_aliases_to_shell_config()
                assert success is True

                # Try adding again - should detect existing aliases
                success = add_aliases_to_shell_config()
                assert success is True

                # Get the actual path that was used
                with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                    profile_path = get_shell_config_path()

                # Check that aliases weren't duplicated
                with open(profile_path, 'r') as f:
                    content = f.read()
                    # Count occurrences of the alias
                    openhands_count = content.count('alias openhands=')
                    oh_count = content.count('alias oh=')
                    assert openhands_count == 1
                    assert oh_count == 1


def test_aliases_exist_in_shell_config_no_file():
    """Test alias detection when no shell config exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                assert aliases_exist_in_shell_config() is False


def test_aliases_exist_in_shell_config_no_aliases():
    """Test alias detection when shell config exists but has no aliases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                # Create bash profile with other content
                profile_path = get_shell_config_path()
                with open(profile_path, 'w') as f:
                    f.write('export PATH=$PATH:/usr/local/bin\n')

                assert aliases_exist_in_shell_config() is False


def test_aliases_exist_in_shell_config_with_aliases():
    """Test alias detection when aliases exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mock shellingham to return bash
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                # Add aliases first
                add_aliases_to_shell_config()

                assert aliases_exist_in_shell_config() is True


def test_shell_config_manager_basic_functionality():
    """Test basic ShellConfigManager functionality."""
    manager = ShellConfigManager()

    # Test command customization
    custom_manager = ShellConfigManager(command='custom-command')
    assert custom_manager.command == 'custom-command'

    # Test shell type detection from path
    assert manager.get_shell_type_from_path(Path('/home/user/.bashrc')) == 'bash'
    assert manager.get_shell_type_from_path(Path('/home/user/.zshrc')) == 'zsh'
    assert (
        manager.get_shell_type_from_path(Path('/home/user/.config/fish/config.fish'))
        == 'fish'
    )


def test_shell_config_manager_reload_commands():
    """Test reload command generation."""
    manager = ShellConfigManager()

    # Test different shell reload commands
    assert 'source ~/.zshrc' in manager.get_reload_command(Path('/home/user/.zshrc'))
    assert 'source ~/.bashrc' in manager.get_reload_command(Path('/home/user/.bashrc'))
    assert 'source ~/.bash_profile' in manager.get_reload_command(
        Path('/home/user/.bash_profile')
    )
    assert 'source ~/.config/fish/config.fish' in manager.get_reload_command(
        Path('/home/user/.config/fish/config.fish')
    )


def test_shell_config_manager_template_rendering():
    """Test that templates are properly rendered."""
    manager = ShellConfigManager(command='test-command')

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Create a bash config file
            bashrc = Path(temp_dir) / '.bashrc'
            bashrc.touch()

            # Mock shell detection
            with patch.object(manager, 'detect_shell', return_value='bash'):
                success = manager.add_aliases()
                assert success is True

                # Check that the custom command was used
                with open(bashrc, 'r') as f:
                    content = f.read()
                    assert 'test-command' in content
                    assert 'alias openhands="test-command"' in content
                    assert 'alias oh="test-command"' in content


def test_alias_setup_declined_false():
    """Test alias setup declined check when marker file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            assert alias_setup_declined() is False


def test_alias_setup_declined_true():
    """Test alias setup declined check when marker file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Create the marker file
            mark_alias_setup_declined()
            assert alias_setup_declined() is True


def test_mark_alias_setup_declined():
    """Test marking alias setup as declined creates the marker file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Initially should be False
            assert alias_setup_declined() is False

            # Mark as declined
            mark_alias_setup_declined()

            # Should now be True
            assert alias_setup_declined() is True

            # Verify the file exists
            marker_file = Path(temp_dir) / '.openhands' / '.cli_alias_setup_declined'
            assert marker_file.exists()


def test_alias_setup_declined_persisted():
    """Test that when user declines alias setup, their choice is persisted."""
    config = OpenHandsConfig()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                with patch(
                    'openhands.cli.shell_config.aliases_exist_in_shell_config',
                    return_value=False,
                ):
                    with patch(
                        'openhands.cli.main.cli_confirm', return_value=1
                    ):  # User chooses "No"
                        with patch('prompt_toolkit.print_formatted_text'):
                            # Initially, user hasn't declined
                            assert not alias_setup_declined()

                            # Run the alias setup flow
                            run_alias_setup_flow(config)

                            # After declining, the marker should be set
                            assert alias_setup_declined()


def test_alias_setup_skipped_when_previously_declined():
    """Test that alias setup is skipped when user has previously declined."""
    OpenHandsConfig()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            # Mark that user has previously declined
            mark_alias_setup_declined()
            assert alias_setup_declined()

            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                with patch(
                    'openhands.cli.shell_config.aliases_exist_in_shell_config',
                    return_value=False,
                ):
                    with patch('openhands.cli.main.cli_confirm'):
                        with patch('prompt_toolkit.print_formatted_text'):
                            # This should not show the setup flow since user previously declined
                            # We test this by checking the main logic conditions

                            should_show = (
                                not aliases_exist_in_shell_config()
                                and not main_alias_setup_declined()
                            )

                            assert not should_show, (
                                'Alias setup should be skipped when user previously declined'
                            )


def test_alias_setup_accepted_does_not_set_declined_flag():
    """Test that when user accepts alias setup, no declined marker is created."""
    config = OpenHandsConfig()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                with patch(
                    'openhands.cli.shell_config.aliases_exist_in_shell_config',
                    return_value=False,
                ):
                    with patch(
                        'openhands.cli.main.cli_confirm', return_value=0
                    ):  # User chooses "Yes"
                        with patch(
                            'openhands.cli.shell_config.add_aliases_to_shell_config',
                            return_value=True,
                        ):
                            with patch('prompt_toolkit.print_formatted_text'):
                                # Initially, user hasn't declined
                                assert not alias_setup_declined()

                                # Run the alias setup flow
                                run_alias_setup_flow(config)

                                # After accepting, the declined marker should still be False
                                assert not alias_setup_declined()
