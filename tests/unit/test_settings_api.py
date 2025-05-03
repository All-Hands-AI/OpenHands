from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.server.app import app
from openhands.server.user_auth.user_auth import UserAuth
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.settings.secret_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore


class MockUserAuth(UserAuth):
    """Mock implementation of UserAuth for testing"""

    def __init__(self):
        self._settings = None
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=None)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token')

    async def get_provider_tokens(self) -> dict[ProviderType, ProviderToken] | None:  # noqa: E501
        return None

    async def get_user_settings_store(self) -> SettingsStore | None:
        return self._settings_store

    async def get_secrets_store(self) -> SecretsStore | None:
        return None

    async def get_user_secrets(self) -> UserSecrets | None:
        return None

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        return MockUserAuth()


@pytest.fixture
def test_client():
    # Create a test client
    with (
        patch(
            'openhands.server.user_auth.user_auth.UserAuth.get_instance',
            return_value=MockUserAuth(),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
    ):
        client = TestClient(app)
        yield client


@pytest.mark.asyncio
async def test_settings_api_endpoints(test_client):
    """Test that the settings API endpoints work with the new auth system"""

    # Test data with remote_runtime_resource_factor
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': 'test-key',
        'llm_base_url': 'https://test.com',
        'remote_runtime_resource_factor': 2,
    }

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)

    # We're not checking the exact response, just that it doesn't error
    assert response.status_code == 200

    # Test the GET settings endpoint
    response = test_client.get('/api/settings')
    assert response.status_code == 200

    # Test updating with partial settings
    partial_settings = {
        'language': 'fr',
        'llm_model': None,  # Should preserve existing value
        'llm_api_key': None,  # Should preserve existing value
    }

    response = test_client.post('/api/settings', json=partial_settings)
    assert response.status_code == 200

    # Test the unset-provider-tokens endpoint
    response = test_client.post('/api/unset-provider-tokens')
    assert response.status_code == 200
