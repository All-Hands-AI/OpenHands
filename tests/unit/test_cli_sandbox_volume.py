"""Test for CLI sandbox volume settings persistence.

This test verifies that sandbox volume settings are properly saved to disk
and loaded when starting a new CLI session, ensuring that the setting persists
across sessions just like other settings such as LLM model and API key.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from openhands.cli.settings import modify_workspace_settings
from openhands.core.config import OpenHandsConfig
from openhands.storage import get_file_store
from openhands.storage.settings.file_settings_store import FileSettingsStore


class TestSandboxVolume:
    """Test class for sandbox volume persistence in CLI."""

    @pytest.mark.asyncio
    async def test_sandbox_volume_persistence(self):
        """Test sandbox volume persistence end-to-end.

        This test verifies that:
        1. Sandbox volume settings can be modified through the settings menu
        2. The settings are properly saved to disk
        3. The settings are loaded when starting a new CLI session
        4. The sandbox volume setting is applied to the config
        """
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a real file store and settings store
            file_store = get_file_store('local', temp_dir)
            settings_store = FileSettingsStore(file_store)

            # Create a config
            config = OpenHandsConfig()
            config.sandbox.volumes = None  # Initially no sandbox volumes

            # Set up test volume
            test_volume = '/test/host:/test/container:rw'

            # PART 1: Simulate user changing settings through the settings menu
            with patch(
                'openhands.cli.settings.cli_confirm', side_effect=[0]
            ):  # Yes to configure volumes
                with patch(
                    'openhands.cli.settings.get_validated_input',
                    return_value=test_volume,
                ):
                    with patch(
                        'openhands.cli.settings.save_settings_confirmation',
                        return_value=True,
                    ):
                        with patch('openhands.cli.settings.print_formatted_text'):
                            with patch('openhands.cli.settings.PromptSession'):
                                # Directly call modify_workspace_settings to simulate user changing settings
                                await modify_workspace_settings(config, settings_store)

            # Verify that the config was updated in memory
            assert config.sandbox.volumes == test_volume

            # PART 2: Verify settings were properly saved to disk
            settings_file_path = os.path.join(temp_dir, 'settings.json')
            assert os.path.exists(settings_file_path), 'Settings file was not created'

            # Read the settings file directly to verify the content
            with open(settings_file_path, 'r') as f:
                settings_data = json.load(f)

            assert settings_data['sandbox_volumes'] == test_volume

            # PART 3: Simulate starting a new CLI session
            # Reset the config to simulate a new session
            new_config = OpenHandsConfig()
            new_config.sandbox.volumes = None

            # Load settings as would happen in a new session
            loaded_settings = await settings_store.load()

            # Apply settings to config as would happen in main_with_loop
            if loaded_settings and loaded_settings.sandbox_volumes:
                new_config.sandbox.volumes = loaded_settings.sandbox_volumes

            # PART 4: Verify the setting was preserved and applied to the new config
            assert new_config.sandbox.volumes == test_volume, (
                'Sandbox volume setting was not preserved'
            )
