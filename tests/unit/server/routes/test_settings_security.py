"""Security tests for settings API to ensure pro-only features are properly validated on backend."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.server.app import app
from openhands.server.types import AppMode
from openhands.server.user_auth.user_auth import UserAuth
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.settings.settings_store import SettingsStore


class MockUserAuthNonPro(UserAuth):
    """Mock implementation of UserAuth for non-pro user testing"""

    def __init__(self):
        self._settings = None
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=None)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user-nonpro'

    async def get_user_email(self) -> str | None:
        return 'nonpro@test.com'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token-nonpro')

    async def get_provider_tokens(self) -> dict[ProviderType, ProviderToken] | None:
        return None

    async def get_user_settings_store(self) -> SettingsStore | None:
        return self._settings_store

    async def get_secrets_store(self) -> SecretsStore | None:
        return None

    async def get_user_secrets(self) -> UserSecrets | None:
        return None

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        return MockUserAuthNonPro()


class MockUserAuthPro(UserAuth):
    """Mock implementation of UserAuth for pro user testing"""

    def __init__(self):
        self._settings = None
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=None)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user-pro'

    async def get_user_email(self) -> str | None:
        return 'pro@test.com'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token-pro')

    async def get_provider_tokens(self) -> dict[ProviderType, ProviderToken] | None:
        return None

    async def get_user_settings_store(self) -> SettingsStore | None:
        return self._settings_store

    async def get_secrets_store(self) -> SecretsStore | None:
        return None

    async def get_user_secrets(self) -> UserSecrets | None:
        return None

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        return MockUserAuthPro()


@pytest.fixture
def test_client_non_pro():
    """Test client for non-pro user"""
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.UserAuth.get_instance',
            return_value=MockUserAuthNonPro(),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
        # Mock the validation function at the routes level to return False (no access)
        patch(
            'openhands.server.routes.settings.validate_llm_settings_access',
            AsyncMock(return_value=False),
        ),
    ):
        client = TestClient(app)
        yield client


@pytest.fixture
def test_client_pro():
    """Test client for pro user"""
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.UserAuth.get_instance',
            return_value=MockUserAuthPro(),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
        # Mock the validation function at the routes level to return True (has access)
        patch(
            'openhands.server.routes.settings.validate_llm_settings_access',
            AsyncMock(return_value=True),
        ),
    ):
        client = TestClient(app)
        yield client


# Test data constants
OPENHANDS_PRO_MODELS = [
    'openhands/claude-sonnet-4-20250514',
    'openhands/gpt-5-2025-08-07',
    'openhands/gpt-5-mini-2025-08-07',
    'openhands/claude-opus-4-20250514',
    'openhands/claude-opus-4-1-20250805',
    'openhands/gemini-2.5-pro',
    'openhands/o3',
    'openhands/o4-mini',
]

DEFAULT_MODEL = 'claude-sonnet-4-20250514'

USER_PROVIDED_MODELS = [
    'anthropic/claude-3-5-sonnet-20241022',
    'openai/gpt-4o',
    'mistral/mistral-large',
]


# Helper functions
def create_base_settings(**overrides):
    """Create base settings data with optional overrides"""
    base_settings = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
    }
    base_settings.update(overrides)
    return base_settings


def assert_forbidden_response(response, model_or_setting_name=''):
    """Assert that response is 403 with subscription-related error"""
    assert response.status_code == 403, (
        f'{model_or_setting_name} should be forbidden for non-pro users'
    )
    response_data = response.json()
    assert any(
        keyword in response_data.get('detail', '').lower()
        or keyword in response_data.get('error', '').lower()
        for keyword in ['subscription', 'pro', 'upgrade']
    )


@pytest.mark.parametrize(
    'model',
    [
        'openhands/claude-sonnet-4-20250514',
        'openhands/gpt-5-2025-08-07',
        'openhands/claude-opus-4-20250514',
        DEFAULT_MODEL,
    ]
    + USER_PROVIDED_MODELS,
)
@pytest.mark.asyncio
async def test_non_pro_user_cannot_set_any_llm_model(test_client_non_pro, model):
    """SECURITY TEST: Non-pro user should not be able to set any LLM model"""
    settings_data = create_base_settings(llm_model=model, llm_api_key='test-key')
    response = test_client_non_pro.post('/api/settings', json=settings_data)
    assert_forbidden_response(response, f'Model {model}')


@pytest.mark.parametrize(
    'llm_setting,value',
    [
        ('llm_api_key', 'new-api-key'),
        ('llm_base_url', 'https://custom-api.example.com'),
        ('llm_model', DEFAULT_MODEL),
        ('confirmation_mode', True),
        ('security_analyzer', 'llm'),
        ('enable_default_condenser', False),
        ('condenser_max_size', 50),
    ],
)
@pytest.mark.asyncio
async def test_non_pro_user_cannot_set_individual_llm_settings(
    test_client_non_pro, llm_setting, value
):
    """SECURITY TEST: Non-pro user should not be able to set individual LLM settings"""
    settings_data = create_base_settings(**{llm_setting: value})
    response = test_client_non_pro.post('/api/settings', json=settings_data)
    assert_forbidden_response(response, f'LLM setting {llm_setting}')


@pytest.mark.asyncio
async def test_non_pro_user_can_set_non_llm_settings(test_client_non_pro):
    """Non-pro users should still be able to modify non-LLM settings"""
    # Only use settings that definitely don't trigger LLM validation
    settings_data = {
        'language': 'fr',
        'max_iterations': 50,
        'user_consents_to_analytics': True,
        'git_user_name': 'test-user',
        'git_user_email': 'test@example.com',
    }
    response = test_client_non_pro.post('/api/settings', json=settings_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_pro_user_can_set_llm_models(test_client_pro):
    """Pro user should be able to set any LLM models"""
    settings_data = create_base_settings(
        llm_model='openhands/claude-sonnet-4-20250514', llm_api_key='test-key'
    )
    response = test_client_pro.post('/api/settings', json=settings_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_expired_subscription_cannot_access_llm_settings():
    """SECURITY TEST: User with expired subscription should not access LLM settings"""
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.UserAuth.get_instance',
            return_value=MockUserAuthPro(),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
        # Mock validation to return False (expired subscription, no access)
        patch(
            'openhands.server.routes.settings.validate_llm_settings_access',
            AsyncMock(return_value=False),
        ),
    ):
        client = TestClient(app)
        settings_data = create_base_settings(
            llm_model='openhands/claude-sonnet-4-20250514', llm_api_key='test-key'
        )
        response = client.post('/api/settings', json=settings_data)
        assert_forbidden_response(response, 'Expired subscription')


@pytest.mark.asyncio
async def test_direct_api_bypass_prevention(test_client_non_pro):
    """SECURITY TEST: Direct API calls should still validate subscription status"""
    settings_data = create_base_settings(
        llm_model='openhands/claude-sonnet-4-20250514',
        llm_api_key='fake-api-key',
        llm_base_url='https://api.anthropic.com',
        remote_runtime_resource_factor=4,
    )

    response = test_client_non_pro.post(
        '/api/settings',
        json=settings_data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'DirectAPIClient/1.0',
        },
    )
    assert_forbidden_response(response, 'Direct API bypass attempt')


@pytest.mark.parametrize(
    'malicious_model',
    [
        'openhands/claude-sonnet-4-20250514',  # Direct
        'OPENHANDS/claude-sonnet-4-20250514',  # Case manipulation
        ' openhands/claude-sonnet-4-20250514',  # Leading space
        'openhands//claude-sonnet-4-20250514',  # Double slash
    ],
)
@pytest.mark.asyncio
async def test_model_prefix_bypass_attempts_blocked(
    test_client_non_pro, malicious_model
):
    """SECURITY TEST: Various prefix bypass attempts should be blocked"""
    settings_data = create_base_settings(
        llm_model=malicious_model, llm_api_key='test-key'
    )
    response = test_client_non_pro.post('/api/settings', json=settings_data)
    assert_forbidden_response(
        response, f"Bypass attempt with model '{malicious_model}'"
    )
