from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from openhands.core.config.sandbox_config import SandboxConfig
from openhands.server.app import app
from openhands.server.settings import Settings


@pytest.fixture
def test_client():
    # Mock the middleware that adds github_token
    class MockMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope['type'] == 'http':
                scope['state'] = {'github_token': 'test-token'}
            await self.app(scope, receive, send)

    # Replace the middleware
    app.middleware_stack = None  # Clear existing middleware
    app.add_middleware(MockMiddleware)

    return TestClient(app)


@pytest.fixture
def mock_settings_store():
    with patch('openhands.server.routes.settings.SettingsStoreImpl') as mock:
        store_instance = MagicMock()
        mock.get_instance = AsyncMock(return_value=store_instance)
        store_instance.load = AsyncMock()
        store_instance.store = AsyncMock()
        yield store_instance


@pytest.mark.asyncio
async def test_settings_api_runtime_factor(test_client, mock_settings_store):
    # Mock the settings store to return None initially (no existing settings)
    mock_settings_store.load.return_value = None

    # Test data with remote_runtime_resource_factor
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': None,
        'llm_base_url': 'https://test.com',
        'remote_runtime_resource_factor': 2,
    }

    # The test_client fixture already handles authentication

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the correct runtime factor
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.remote_runtime_resource_factor == 2

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    assert response.status_code == 200
    assert response.json()['remote_runtime_resource_factor'] == 2

    # Verify that the sandbox config gets updated when settings are loaded
    with patch('openhands.server.shared.config') as mock_config:
        mock_config.sandbox = SandboxConfig()
        response = test_client.get('/api/settings')
        assert response.status_code == 200

        # Verify that the sandbox config was updated with the new value
        mock_settings_store.store.assert_called()
        stored_settings = mock_settings_store.store.call_args[0][0]
        assert stored_settings.remote_runtime_resource_factor == 2
