from unittest.mock import ANY, MagicMock, patch

from openhands.core.config import OpenHandsConfig


class TestViMode:
    """Test the VI mode feature."""

    @patch('openhands.cli.tui.PromptSession')
    def test_create_prompt_session_vi_mode_enabled(self, mock_prompt_session):
        """Test that vi_mode can be enabled."""
        from openhands.cli.tui import create_prompt_session

        config = OpenHandsConfig(vi_mode=True)
        create_prompt_session(config)
        mock_prompt_session.assert_called_with(
            style=ANY,
            vi_mode=True,
        )

    @patch('openhands.cli.tui.PromptSession')
    def test_create_prompt_session_vi_mode_disabled(self, mock_prompt_session):
        """Test that vi_mode is disabled by default."""
        from openhands.cli.tui import create_prompt_session

        config = OpenHandsConfig(vi_mode=False)
        create_prompt_session(config)
        mock_prompt_session.assert_called_with(
            style=ANY,
            vi_mode=False,
        )

    @patch('openhands.cli.tui.Application')
    def test_cli_confirm_vi_keybindings_are_added(self, mock_app_class):
        """Test that vi keybindings are added to the KeyBindings object."""
        from openhands.cli.tui import cli_confirm

        config = OpenHandsConfig(vi_mode=True)
        with patch('openhands.cli.tui.KeyBindings', MagicMock()) as mock_key_bindings:
            cli_confirm(
                config, 'Test question', choices=['Choice 1', 'Choice 2', 'Choice 3']
            )
            # here we are checking if the key bindings are being created
            assert mock_key_bindings.call_count == 1

            # then we check that the key bindings are being added
            mock_kb_instance = mock_key_bindings.return_value
            assert mock_kb_instance.add.call_count > 0

    @patch('openhands.cli.tui.Application')
    def test_cli_confirm_vi_keybindings_are_not_added(self, mock_app_class):
        """Test that vi keybindings are not added when vi_mode is False."""
        from openhands.cli.tui import cli_confirm

        config = OpenHandsConfig(vi_mode=False)
        with patch('openhands.cli.tui.KeyBindings', MagicMock()) as mock_key_bindings:
            cli_confirm(
                config, 'Test question', choices=['Choice 1', 'Choice 2', 'Choice 3']
            )
            # here we are checking if the key bindings are being created
            assert mock_key_bindings.call_count == 1

            # then we check that the key bindings are being added
            mock_kb_instance = mock_key_bindings.return_value

            # and here we check that the vi key bindings are not being added
            for call in mock_kb_instance.add.call_args_list:
                assert call[0][0] not in ('j', 'k')

    @patch('openhands.cli.tui.Application')
    def test_cli_confirm_vi_hotkeys_are_added(self, mock_app_class):
        """Test that vi hotkeys (j, k) are added to the KeyBindings object."""
        from openhands.cli.tui import cli_confirm

        config = OpenHandsConfig(vi_mode=True)
        with patch('openhands.cli.tui.KeyBindings', MagicMock()) as mock_key_bindings:
            cli_confirm(
                config, 'Test question', choices=['Choice 1', 'Choice 2', 'Choice 3']
            )
            # here we are checking if the key bindings are being created
            assert mock_key_bindings.call_count == 1

            # then we check that the key bindings are being added
            mock_kb_instance = mock_key_bindings.return_value
            assert mock_kb_instance.add.call_count > 0

            # and here we check that the vi key bindings are being added
            j_called = False
            k_called = False
            for call in mock_kb_instance.add.call_args_list:
                if call[0][0] == 'j':
                    j_called = True
                if call[0][0] == 'k':
                    k_called = True

            assert j_called, "The 'j' key should be bound in vi_mode"
            assert k_called, "The 'k' key should be bound in vi_mode"
