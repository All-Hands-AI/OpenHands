"""Unit tests for CLI alias setup persistence functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from openhands.cli.main import run_alias_setup_flow
from openhands.cli.shell_config import alias_setup_declined, mark_alias_setup_declined
from openhands.core.config import OpenHandsConfig


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
                        'openhands.cli.main.global_openhands_command_exists',
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
                    with patch(
                        'openhands.cli.main.global_openhands_command_exists',
                        return_value=False,
                    ):
                        with patch('openhands.cli.main.cli_confirm'):
                            with patch('prompt_toolkit.print_formatted_text'):
                                # This should not show the setup flow since user previously declined
                                # We test this by checking the main logic conditions
                                from openhands.cli.main import (
                                    alias_setup_declined as main_alias_setup_declined,
                                )
                                from openhands.cli.main import (
                                    aliases_exist_in_shell_config,
                                    global_openhands_command_exists,
                                )

                                should_show = (
                                    not aliases_exist_in_shell_config()
                                    and not global_openhands_command_exists()
                                    and not main_alias_setup_declined()
                                )

                                assert not should_show, (
                                    'Alias setup should be skipped when user previously declined'
                                )


def test_alias_setup_skipped_when_global_command_exists():
    """Test that alias setup is skipped when global openhands command exists."""
    # This test now checks the main logic conditions since the function
    # no longer handles the global command check internally
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('openhands.cli.shell_config.Path.home', return_value=Path(temp_dir)):
            with patch('shellingham.detect_shell', return_value=('bash', 'bash')):
                with patch(
                    'openhands.cli.shell_config.aliases_exist_in_shell_config',
                    return_value=False,
                ):
                    with patch(
                        'openhands.cli.main.global_openhands_command_exists',
                        return_value=True,
                    ):
                        # Test the main logic conditions
                        from openhands.cli.main import (
                            alias_setup_declined as main_alias_setup_declined,
                        )
                        from openhands.cli.main import (
                            aliases_exist_in_shell_config,
                            global_openhands_command_exists,
                        )

                        should_show = (
                            not aliases_exist_in_shell_config()
                            and not global_openhands_command_exists()
                            and not main_alias_setup_declined()
                        )

                        assert not should_show, (
                            'Alias setup should be skipped when global command exists'
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
                        'openhands.cli.main.global_openhands_command_exists',
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
