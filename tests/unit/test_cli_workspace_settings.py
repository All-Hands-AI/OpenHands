"""Test CLI workspace settings functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.cli.settings import modify_workspace_settings
from openhands.core.config import OpenHandsConfig
from openhands.storage.data_models.settings import Settings
from openhands.storage.settings.file_settings_store import FileSettingsStore


@pytest.fixture
def mock_settings_store():
    """Create a mock settings store."""
    store = MagicMock(spec=FileSettingsStore)
    store.load = AsyncMock(return_value=Settings())
    store.store = AsyncMock()
    return store


@pytest.fixture
def config():
    """Create a config for testing."""
    config = OpenHandsConfig()
    config.workspace_base = '/test/workspace'
    config.sandbox.volumes = '/host:/container:rw'
    return config


@pytest.mark.asyncio
@patch('openhands.cli.settings.PromptSession')
@patch('openhands.cli.settings.cli_confirm')
@patch('openhands.cli.settings.print_formatted_text')
@patch('openhands.cli.settings.get_validated_input')
@patch('openhands.cli.settings.save_settings_confirmation')
async def test_modify_workspace_settings_no_changes(
    mock_save_confirmation,
    mock_get_input,
    mock_print,
    mock_confirm,
    mock_session,
    config,
    mock_settings_store,
):
    """Test modify_workspace_settings with no changes."""
    # Mock user choosing not to change workspace or volumes
    mock_confirm.side_effect = [1, 1]  # No for workspace, No for volumes

    await modify_workspace_settings(config, mock_settings_store)

    # Verify the settings store was not called to store settings
    mock_settings_store.store.assert_not_called()
    # Verify the config was not changed
    assert config.workspace_base == '/test/workspace'
    assert config.sandbox.volumes == '/host:/container:rw'


@pytest.mark.asyncio
@patch('openhands.cli.settings.PromptSession')
@patch('openhands.cli.settings.cli_confirm')
@patch('openhands.cli.settings.print_formatted_text')
@patch('openhands.cli.settings.get_validated_input')
@patch('openhands.cli.settings.save_settings_confirmation')
@patch('os.path.isdir')
async def test_modify_workspace_settings_change_workspace(
    mock_isdir,
    mock_save_confirmation,
    mock_get_input,
    mock_print,
    mock_confirm,
    mock_session,
    config,
    mock_settings_store,
):
    """Test modify_workspace_settings with workspace change."""
    # Mock directory exists
    mock_isdir.return_value = True
    # Mock user choosing to change workspace but not volumes
    mock_confirm.side_effect = [0, 1]  # Yes for workspace, No for volumes
    # Mock user input for new workspace
    mock_get_input.return_value = '/new/workspace'
    # Mock user confirming to save settings
    mock_save_confirmation.return_value = True

    await modify_workspace_settings(config, mock_settings_store)

    # Verify the settings store was called to store settings
    mock_settings_store.store.assert_called_once()
    # Verify the config was changed
    assert config.workspace_base == '/new/workspace'
    assert config.sandbox.volumes == '/host:/container:rw'


@pytest.mark.asyncio
@patch('openhands.cli.settings.PromptSession')
@patch('openhands.cli.settings.cli_confirm')
@patch('openhands.cli.settings.print_formatted_text')
@patch('openhands.cli.settings.get_validated_input')
@patch('openhands.cli.settings.save_settings_confirmation')
async def test_modify_workspace_settings_change_volumes(
    mock_save_confirmation,
    mock_get_input,
    mock_print,
    mock_confirm,
    mock_session,
    config,
    mock_settings_store,
):
    """Test modify_workspace_settings with volumes change."""
    # Mock user choosing not to change workspace but to change volumes
    mock_confirm.side_effect = [1, 0]  # No for workspace, Yes for volumes
    # Mock user input for new volumes
    mock_get_input.return_value = '/new/host:/new/container:ro'
    # Mock user confirming to save settings
    mock_save_confirmation.return_value = True

    await modify_workspace_settings(config, mock_settings_store)

    # Verify the settings store was called to store settings
    mock_settings_store.store.assert_called_once()
    # Verify the config was changed
    assert config.workspace_base == '/test/workspace'
    assert config.sandbox.volumes == '/new/host:/new/container:ro'


@pytest.mark.asyncio
@patch('openhands.cli.settings.PromptSession')
@patch('openhands.cli.settings.cli_confirm')
@patch('openhands.cli.settings.print_formatted_text')
@patch('openhands.cli.settings.get_validated_input')
@patch('openhands.cli.settings.save_settings_confirmation')
async def test_modify_workspace_settings_invalid_volumes(
    mock_save_confirmation,
    mock_get_input,
    mock_print,
    mock_confirm,
    mock_session,
    config,
    mock_settings_store,
):
    """Test modify_workspace_settings with invalid volumes format."""
    # Mock user choosing not to change workspace but to change volumes
    mock_confirm.side_effect = [
        1,
        0,
        0,
    ]  # No for workspace, Yes for volumes, Yes to proceed anyway
    # Mock user input for new volumes (invalid format)
    mock_get_input.return_value = 'invalid-format'
    # Mock user confirming to save settings
    mock_save_confirmation.return_value = True

    await modify_workspace_settings(config, mock_settings_store)

    # Verify the settings store was called to store settings
    mock_settings_store.store.assert_called_once()
    # Verify the config was changed despite invalid format (user confirmed)
    assert config.workspace_base == '/test/workspace'
    assert config.sandbox.volumes == 'invalid-format'


@pytest.mark.asyncio
@patch('openhands.cli.settings.PromptSession')
@patch('openhands.cli.settings.cli_confirm')
@patch('openhands.cli.settings.print_formatted_text')
@patch('openhands.cli.settings.get_validated_input')
@patch('openhands.cli.settings.save_settings_confirmation')
async def test_modify_workspace_settings_cancel_invalid_volumes(
    mock_save_confirmation,
    mock_get_input,
    mock_print,
    mock_confirm,
    mock_session,
    config,
    mock_settings_store,
):
    """Test modify_workspace_settings with invalid volumes format and user cancellation."""
    # Mock user choosing not to change workspace but to change volumes
    mock_confirm.side_effect = [
        1,
        0,
        1,
    ]  # No for workspace, Yes for volumes, No to proceed with invalid format
    # Mock user input for new volumes (invalid format)
    mock_get_input.return_value = 'invalid-format'

    await modify_workspace_settings(config, mock_settings_store)

    # Verify the settings store was not called to store settings
    mock_settings_store.store.assert_not_called()
    # Verify the config was not changed
    assert config.workspace_base == '/test/workspace'
    assert config.sandbox.volumes == '/host:/container:rw'
