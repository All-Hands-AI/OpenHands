"""Integration test for MCP settings merging in the full flow."""

from unittest.mock import AsyncMock, patch

import pytest

from openhands.server.user_auth.default_user_auth import DefaultUserAuth
from openhands.storage.settings.file_settings_store import FileSettingsStore


@pytest.mark.asyncio
async def test_user_auth_no_stored_settings():
    """Test behavior when no settings are stored (first time user)."""
    user_auth = DefaultUserAuth()

    # Mock settings store to return None (no stored settings)
    mock_settings_store = AsyncMock(spec=FileSettingsStore)
    mock_settings_store.load.return_value = None

    with patch.object(
        user_auth, 'get_user_settings_store', return_value=mock_settings_store
    ):
        settings = await user_auth.get_user_settings()

    # Should return None when no settings are stored
    assert settings is None
