import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.cli.main import run_setup_flow
from openhands.core.config import OpenHandsConfig
from openhands.storage.settings.file_settings_store import FileSettingsStore


class TestCLISetupFlow(unittest.TestCase):
    """Test the CLI setup flow."""

    @patch('openhands.cli.settings.modify_llm_settings_basic')
    @patch('openhands.cli.main.print_formatted_text')
    async def test_run_setup_flow(self, mock_print, mock_modify_settings):
        """Test that the setup flow calls the modify_llm_settings_basic function."""
        # Setup
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)
        mock_modify_settings.return_value = None

        # Execute
        await run_setup_flow(config, settings_store)

        # Verify
        mock_modify_settings.assert_called_once_with(config, settings_store)
        # Verify that print_formatted_text was called at least twice (for welcome message and instructions)
        self.assertGreaterEqual(mock_print.call_count, 2)

    @patch('openhands.cli.main.run_setup_flow')
    @patch('openhands.cli.main.FileSettingsStore.get_instance')
    @patch('openhands.cli.main.setup_config_from_args')
    @patch('openhands.cli.main.parse_arguments')
    async def test_main_calls_setup_flow_when_no_settings(
        self, mock_parse_args, mock_setup_config, mock_get_instance, mock_run_setup_flow
    ):
        """Test that main calls run_setup_flow when no settings are found."""
        # Setup
        mock_args = MagicMock()
        mock_config = MagicMock(spec=OpenHandsConfig)
        mock_settings_store = AsyncMock(spec=FileSettingsStore)

        # First load returns None (no settings), second load returns settings after setup
        mock_settings_store.load = AsyncMock(side_effect=[None, MagicMock()])

        mock_parse_args.return_value = mock_args
        mock_setup_config.return_value = mock_config
        mock_get_instance.return_value = mock_settings_store
        mock_run_setup_flow.return_value = None

        # Import here to avoid circular imports during patching
        from openhands.cli.main import main

        # Execute
        loop = asyncio.get_event_loop()
        await main(loop)

        # Verify
        mock_run_setup_flow.assert_called_once_with(mock_config, mock_settings_store)
        # Verify that load was called twice (once before setup, once after)
        self.assertEqual(mock_settings_store.load.call_count, 2)


def run_async_test(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    unittest.main()
