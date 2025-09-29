"""
Tests for LLM settings PRO validation with strict security policy.

STRICT SECURITY POLICY: Non-PRO users in SaaS mode cannot include ANY LLM settings 
in their requests, regardless of whether they are changing them or not.

These tests demonstrate the expected behavior:
1. Non-PRO users should receive 403 for ANY request containing LLM settings
2. Non-PRO users can only change non-LLM settings in requests that contain NO LLM settings
3. PRO users should be able to change any settings
"""

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
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.settings.settings_store import SettingsStore


class MockUserAuthNonPro(UserAuth):
    """Mock implementation of UserAuth for non-pro user testing"""

    def __init__(self, existing_settings=None):
        self._settings = existing_settings
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=existing_settings)
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
        return cls()


class MockUserAuthPro(UserAuth):
    """Mock implementation of UserAuth for pro user testing"""

    def __init__(self, existing_settings=None):
        self._settings = existing_settings
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=existing_settings)
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
        return cls()


def create_existing_settings_with_llm():
    """Create existing settings that include LLM configuration"""
    return Settings(
        language='en',
        agent='CodeActAgent',  # LLM setting
        llm_model='anthropic/claude-3-5-sonnet-20241022',  # LLM setting
        llm_api_key=SecretStr('sk-existing-key'),  # LLM setting
        llm_base_url='https://api.anthropic.com',  # LLM setting
        confirmation_mode=True,  # LLM setting
        security_analyzer='llm',  # LLM setting
        enable_default_condenser=True,  # LLM setting
        condenser_max_size=100,  # LLM setting
        search_api_key=SecretStr('search-key'),  # LLM setting
        max_iterations=50,  # Non-LLM setting
        user_consents_to_analytics=True,  # Non-LLM setting
        git_user_name='existing-user',  # Non-LLM setting
        git_user_email='existing@example.com',  # Non-LLM setting
    )


@pytest.fixture
def test_client_non_pro_with_existing_llm():
    """Test client for non-pro user who already has LLM settings configured"""
    existing_settings = create_existing_settings_with_llm()
    
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.get_user_auth',
            AsyncMock(return_value=MockUserAuthNonPro(existing_settings)),
        ),
        patch(
            'openhands.server.user_auth.get_user_id',
            AsyncMock(return_value='test-user-nonpro'),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
    ):
        client = TestClient(app)
        yield client, existing_settings


@pytest.fixture
def test_client_pro_with_existing_llm():
    """Test client for pro user who already has LLM settings configured"""
    existing_settings = create_existing_settings_with_llm()
    
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.get_user_auth',
            AsyncMock(return_value=MockUserAuthPro(existing_settings)),
        ),
        patch(
            'openhands.server.user_auth.get_user_id',
            AsyncMock(return_value='test-user-pro'),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
        # Note: Pro user validation will be handled by the actual implementation
    ):
        client = TestClient(app)
        yield client, existing_settings


@pytest.fixture
def test_client_non_pro_no_existing():
    """Test client for non-pro user with no existing settings"""
    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.get_user_auth',
            AsyncMock(return_value=MockUserAuthNonPro(None)),
        ),
        patch(
            'openhands.server.user_auth.get_user_id',
            AsyncMock(return_value='test-user-nonpro'),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
    ):
        client = TestClient(app)
        yield client


def create_full_settings_payload(existing_settings, **changes):
    """
    Create a full settings payload like the frontend sends.
    This simulates how the frontend merges existing settings with changes.
    """
    # Start with existing settings
    payload = {}
    if existing_settings:
        payload.update({
            'language': existing_settings.language,
            'agent': existing_settings.agent,
            'llm_model': existing_settings.llm_model,
            'llm_api_key': existing_settings.llm_api_key.get_secret_value() if existing_settings.llm_api_key else None,
            'llm_base_url': existing_settings.llm_base_url,
            'confirmation_mode': existing_settings.confirmation_mode,
            'security_analyzer': existing_settings.security_analyzer,
            'enable_default_condenser': existing_settings.enable_default_condenser,
            'condenser_max_size': existing_settings.condenser_max_size,
            'max_iterations': existing_settings.max_iterations,
            'user_consents_to_analytics': existing_settings.user_consents_to_analytics,
        })
    
    # Apply changes
    payload.update(changes)
    
    # Remove None values (frontend doesn't send them)
    return {k: v for k, v in payload.items() if v is not None}


@pytest.mark.asyncio
async def test_non_pro_cannot_change_language_when_request_includes_llm_settings(test_client_non_pro_with_existing_llm):
    """
    SECURITY TEST: Non-pro user should NOT be able to change language when request includes LLM settings.
    
    This enforces the strict security policy where:
    1. User has existing LLM settings (from when they were PRO or from initial setup)
    2. User tries to change language from 'en' to 'fr'
    3. Frontend sends ENTIRE settings object including existing LLM settings
    4. Backend should reject this with 403 because request contains LLM settings
    """
    client, existing_settings = test_client_non_pro_with_existing_llm
    
    # Create payload that includes existing LLM settings + language change
    settings_payload = create_full_settings_payload(existing_settings, language='fr')
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - non-pro user cannot include LLM settings in request
    assert response.status_code == 403, f"Non-pro user should not be able to include LLM settings in request. Got: {response.json()}"
    response_data = response.json()
    assert any(
        keyword in response_data.get('detail', '').lower()
        or keyword in response_data.get('error', '').lower()
        for keyword in ['subscription', 'pro', 'upgrade']
    )


@pytest.mark.asyncio
async def test_non_pro_cannot_change_llm_model_with_existing_settings(test_client_non_pro_with_existing_llm):
    """
    SECURITY TEST: Non-pro user should NOT be able to change LLM model.
    """
    client, existing_settings = test_client_non_pro_with_existing_llm
    
    # Create payload that changes LLM model
    settings_payload = create_full_settings_payload(
        existing_settings, 
        llm_model='openai/gpt-4o'  # Different from existing
    )
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is trying to change LLM model
    assert response.status_code == 403, f"Non-pro user should not be able to change LLM model. Got: {response.json()}"
    response_data = response.json()
    assert any(
        keyword in response_data.get('detail', '').lower()
        or keyword in response_data.get('error', '').lower()
        for keyword in ['subscription', 'pro', 'upgrade']
    )


@pytest.mark.asyncio
async def test_non_pro_cannot_change_llm_api_key_with_existing_settings(test_client_non_pro_with_existing_llm):
    """
    SECURITY TEST: Non-pro user should NOT be able to change LLM API key.
    """
    client, existing_settings = test_client_non_pro_with_existing_llm
    
    # Create payload that changes LLM API key
    settings_payload = create_full_settings_payload(
        existing_settings, 
        llm_api_key='sk-new-different-key'  # Different from existing
    )
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is trying to change LLM API key
    assert response.status_code == 403, f"Non-pro user should not be able to change LLM API key. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_set_initial_llm_settings(test_client_non_pro_no_existing):
    """
    SECURITY TEST: Non-pro user should NOT be able to set LLM settings for the first time.
    """
    client = test_client_non_pro_no_existing
    
    # Create payload with new LLM settings
    settings_payload = {
        'language': 'en',
        'llm_model': 'anthropic/claude-3-5-sonnet-20241022',
        'llm_api_key': 'sk-new-key',
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is trying to set LLM settings for first time
    assert response.status_code == 403, f"Non-pro user should not be able to set initial LLM settings. Got: {response.json()}"


@pytest.mark.asyncio
async def test_pro_user_can_change_llm_settings(test_client_pro_with_existing_llm):
    """
    PRO TEST: Pro user should be able to change any LLM settings.
    """
    client, existing_settings = test_client_pro_with_existing_llm
    
    # Create payload that changes LLM model
    settings_payload = create_full_settings_payload(
        existing_settings, 
        llm_model='openai/gpt-4o',  # Different from existing
        llm_api_key='sk-new-pro-key'  # Different from existing
    )
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should succeed - pro user can change LLM settings
    assert response.status_code == 200, f"Pro user should be able to change LLM settings. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_change_multiple_non_llm_settings_when_request_includes_llm_settings(test_client_non_pro_with_existing_llm):
    """
    SECURITY TEST: Non-pro user should NOT be able to change non-LLM settings when request includes LLM settings.
    """
    client, existing_settings = test_client_non_pro_with_existing_llm
    
    # Create payload that changes multiple non-LLM settings but includes existing LLM settings
    settings_payload = create_full_settings_payload(
        existing_settings, 
        language='es',  # Changed
        max_iterations=75,  # Changed
        user_consents_to_analytics=False  # Changed
    )
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - non-pro user cannot include LLM settings in request
    assert response.status_code == 403, f"Non-pro user should not be able to include LLM settings in request. Got: {response.json()}"
    response_data = response.json()
    assert any(
        keyword in response_data.get('detail', '').lower()
        or keyword in response_data.get('error', '').lower()
        for keyword in ['subscription', 'pro', 'upgrade']
    )


@pytest.mark.asyncio
async def test_non_pro_cannot_change_advanced_llm_settings(test_client_non_pro_with_existing_llm):
    """
    SECURITY TEST: Non-pro user should NOT be able to change advanced LLM settings.
    """
    client, existing_settings = test_client_non_pro_with_existing_llm
    
    # Create payload that changes advanced LLM settings
    settings_payload = create_full_settings_payload(
        existing_settings, 
        confirmation_mode=False,  # Changed from True
        security_analyzer='none',  # Changed from 'llm'
        condenser_max_size=200  # Changed from 100
    )
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is trying to change advanced LLM settings
    assert response.status_code == 403, f"Non-pro user should not be able to change advanced LLM settings. Got: {response.json()}"


# Additional tests to verify correct LLM-only settings identification

@pytest.mark.asyncio
async def test_non_pro_can_change_non_llm_settings_only(test_client_non_pro_no_existing):
    """
    TEST: Non-pro user should be able to change non-LLM settings ONLY.
    
    Non-pro users should NOT be able to include ANY LLM settings in their request,
    even if they're setting them to default values.
    """
    client = test_client_non_pro_no_existing
    
    # Create payload with ONLY non-LLM settings
    settings_payload = {
        # Non-LLM settings changes (should be allowed)
        'language': 'fr',
        'max_iterations': 75,
        'user_consents_to_analytics': True,
        'git_user_name': 'new-user',
        'git_user_email': 'new-user@example.com',
        'enable_sound_notifications': True,
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should succeed - user is only changing non-LLM settings
    assert response.status_code == 200, f"Non-pro user should be able to change non-LLM settings only. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_change_from_default_llm_model(test_client_non_pro_no_existing):
    """
    SECURITY TEST: Non-pro user should NOT be able to change LLM model from default.
    """
    client = test_client_non_pro_no_existing
    
    settings_payload = {
        'llm_model': 'anthropic/claude-3-5-sonnet-20241022',  # Different from default
        'language': 'en',
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is changing LLM model from default
    assert response.status_code == 403, f"Non-pro user should not be able to change LLM model from default. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_set_non_default_llm_api_key(test_client_non_pro_no_existing):
    """
    SECURITY TEST: Non-pro user should NOT be able to set LLM API key to non-default value.
    """
    client = test_client_non_pro_no_existing
    
    settings_payload = {
        'llm_api_key': 'sk-new-key',  # Non-default (default is null/empty)
        'language': 'en',
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is setting LLM API key to non-default
    assert response.status_code == 403, f"Non-pro user should not be able to set LLM API key. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_change_confirmation_mode_from_default(test_client_non_pro_no_existing):
    """
    SECURITY TEST: Non-pro user should NOT be able to change confirmation_mode from default.
    """
    client = test_client_non_pro_no_existing
    
    settings_payload = {
        'confirmation_mode': True,  # Different from default (false)
        'language': 'en',
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - user is changing confirmation_mode from default
    assert response.status_code == 403, f"Non-pro user should not be able to change confirmation_mode from default. Got: {response.json()}"


@pytest.mark.asyncio
async def test_non_pro_cannot_include_any_llm_settings_even_defaults(test_client_non_pro_no_existing):
    """
    SECURITY TEST: Non-pro user should NOT be able to include ANY LLM settings, even defaults.
    
    This tests that non-pro users cannot include LLM settings in their request,
    even if they're setting them to default values.
    """
    client = test_client_non_pro_no_existing
    
    settings_payload = {
        # Including LLM settings (even defaults) should be forbidden
        'llm_model': 'openhands/claude-sonnet-4-20250514',  # Default value but still forbidden
        'confirmation_mode': False,  # Default value but still forbidden
        'security_analyzer': 'llm',  # Default value but still forbidden
        
        # Non-LLM setting
        'language': 'en',
    }
    
    response = client.post('/api/settings', json=settings_payload)
    
    # This should fail - non-pro users cannot include ANY LLM settings
    assert response.status_code == 403, f"Non-pro user should not be able to include ANY LLM settings, even defaults. Got: {response.json()}"


# These tests will FAIL until we implement proper validation logic
# They demonstrate the expected behavior we need to implement:
#
# STRICT SECURITY RULE: Non-PRO users in SaaS mode should NOT be able to include 
# ANY LLM settings in their request, regardless of the values.
#
# LLM-ONLY SETTINGS (forbidden for non-PRO users in SaaS mode):
# - llm_model
# - llm_api_key  
# - llm_base_url
# - search_api_key
# - agent
# - confirmation_mode
# - security_analyzer
# - enable_default_condenser
# - condenser_max_size
#
# NON-LLM SETTINGS (always allowed for non-PRO users when NO LLM settings are in request):
# - language, max_iterations, user_consents_to_analytics, git_user_name, 
#   git_user_email, enable_sound_notifications, etc.
#
# PRO users should be able to modify any settings.
# Non-SaaS mode should allow all settings modifications.

