import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.server.app import app
from openhands.server.user_auth.user_auth import UserAuth
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.settings.settings_store import SettingsStore


class MockUserAuth(UserAuth):
    def __init__(self):
        self._settings = None
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=None)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user'

    async def get_user_email(self) -> str | None:
        return 'test-email@whatever.com'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token')

    async def get_provider_tokens(self):
        return None

    async def get_user_settings_store(self) -> SettingsStore | None:
        return self._settings_store

    async def get_secrets_store(self):
        return None

    async def get_user_secrets(self) -> UserSecrets | None:
        return None

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        return MockUserAuth()


@pytest.fixture
def client_with_temp_config(tmp_path):
    # Use a temp working dir with isolated config.toml
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with (
            patch.dict(os.environ, {'SESSION_API_KEY': ''}, clear=False),
            patch('openhands.server.dependencies._SESSION_API_KEY', None),
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
            yield client, tmp_path
    finally:
        os.chdir(cwd)


@pytest.mark.asyncio
async def test_settings_post_persists_to_toml(client_with_temp_config):
    client, tmp_path = client_with_temp_config

    # POST settings to update/persist LLM fields + search key
    payload = {
        'llm_model': 'persist-model',
        'llm_api_key': 'persist-key',
        'llm_base_url': 'https://persist.example',
        'search_api_key': 'tavily-secret',
    }

    r = client.post('/api/settings', json=payload)
    assert r.status_code == 200

    # Verify config.toml was created and contains expected keys
    toml_file = os.path.join(tmp_path, 'config.toml')
    assert os.path.exists(toml_file)
    content = open(toml_file, 'r', encoding='utf-8').read()

    assert '[llm]' in content
    assert 'model = "persist-model"' in content
    assert 'api_key = "persist-key"' in content
    assert 'base_url = "https://persist.example"' in content

    assert '[core]' in content
    assert 'search_api_key = "tavily-secret"' in content
