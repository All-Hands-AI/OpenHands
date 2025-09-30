"""
Tests for the LLM settings validation bug fix.

This test file specifically addresses the bug where non-PRO users were incorrectly
blocked from editing non-LLM settings because the validation logic was comparing
against default values instead of current values.

BUG SCENARIO:
1. User has existing LLM settings (e.g., from frontend defaults or previous PRO subscription)
2. User tries to change only non-LLM settings (e.g., language)
3. Frontend sends entire settings object (current + changes)
4. Old validation logic compared against defaults and flagged existing LLM settings as "changes"
5. User got 403 error even though they weren't trying to change LLM settings

FIX:
The validation now compares against the user's current stored settings instead of defaults.
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


class MockUserAuthNonProWithExistingSettings(UserAuth):
    """Mock implementation of UserAuth for non-pro user with existing LLM settings"""

    def __init__(self, existing_settings=None):
        self._settings = existing_settings
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=existing_settings)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user-nonpro-with-existing'

    async def get_user_email(self) -> str | None:
        return 'nonpro-existing@test.com'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token-nonpro-existing')

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


def create_existing_settings_like_frontend_defaults():
    """
    Create existing settings that match what a user might have from frontend defaults.
    This simulates a user who has used the app before and has LLM settings configured.
    """
    return Settings(
        language='en',
        agent='CodeActAgent',  # LLM setting - frontend default
        llm_model='openhands/claude-sonnet-4-20250514',  # LLM setting - frontend default
        llm_base_url='',  # LLM setting - frontend default (empty string)
        confirmation_mode=False,  # LLM setting - frontend default
        search_api_key=SecretStr(''),  # LLM setting - frontend default (empty string)
        security_analyzer='llm',  # LLM setting - frontend default
        enable_default_condenser=True,  # LLM setting - frontend default
        condenser_max_size=120,  # LLM setting - frontend default
        max_iterations=50,  # Non-LLM setting
        user_consents_to_analytics=False,  # Non-LLM setting
        enable_sound_notifications=False,  # Non-LLM setting
        git_user_name='openhands',  # Non-LLM setting - frontend default
        git_user_email='openhands@all-hands.dev',  # Non-LLM setting - frontend default
    )


@pytest.fixture
def test_client_non_pro_with_frontend_defaults():
    """Test client for non-pro user who has existing settings from frontend defaults"""
    existing_settings = create_existing_settings_like_frontend_defaults()

    with (
        patch.dict(
            os.environ, {'SESSION_API_KEY': '', 'APP_MODE': 'saas'}, clear=False
        ),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
        patch('openhands.server.shared.server_config.app_mode', AppMode.SAAS),
        patch(
            'openhands.server.user_auth.user_auth.get_user_auth',
            AsyncMock(return_value=MockUserAuthNonProWithExistingSettings(existing_settings)),
        ),
        patch(
            'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
            AsyncMock(return_value=FileSettingsStore(InMemoryFileStore())),
        ),
        patch(
            'enterprise.server.utils.is_pro_user',
            lambda user_id: False,  # Always non-pro for this test
        ),
    ):
        # Override the get_user_id dependency to return the non-pro user ID
        from openhands.server.user_auth import get_user_id

        app.dependency_overrides[get_user_id] = lambda: 'test-user-nonpro-with-existing'

        try:
            client = TestClient(app)
            yield client, existing_settings
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()


def create_frontend_style_payload(existing_settings, **changes):
    """
    Create a payload exactly like the frontend sends.
    The frontend merges current settings with changes and sends the entire object.
    """
    # Start with existing settings (simulating frontend behavior)
    payload = {}
    if existing_settings:
        payload.update({
            'language': existing_settings.language,
            'agent': existing_settings.agent,
            'llm_model': existing_settings.llm_model,
            'llm_base_url': existing_settings.llm_base_url,
            'confirmation_mode': existing_settings.confirmation_mode,
            'security_analyzer': existing_settings.security_analyzer,
            'enable_default_condenser': existing_settings.enable_default_condenser,
            'condenser_max_size': existing_settings.condenser_max_size,
            'max_iterations': existing_settings.max_iterations,
            'user_consents_to_analytics': existing_settings.user_consents_to_analytics,
            'enable_sound_notifications': existing_settings.enable_sound_notifications,
            'git_user_name': existing_settings.git_user_name,
            'git_user_email': existing_settings.git_user_email,
        })
        
        # Handle SecretStr fields
        if existing_settings.search_api_key:
            payload['search_api_key'] = existing_settings.search_api_key.get_secret_value()

    # Apply changes (what the user actually wants to change)
    payload.update(changes)

    # Remove None values (frontend doesn't send them)
    return {k: v for k, v in payload.items() if v is not None}


@pytest.mark.asyncio
async def test_non_pro_can_change_language_with_existing_llm_settings_bug_fix(
    test_client_non_pro_with_frontend_defaults,
):
    """
    BUG FIX TEST: Non-pro user should be able to change language even when they have existing LLM settings.

    This test reproduces the exact bug scenario:
    1. User has existing LLM settings (from frontend defaults or previous usage)
    2. User tries to change language from 'en' to 'es'
    3. Frontend sends entire settings object (existing + language change)
    4. With the fix, validation should compare against current settings and allow the change
    5. Without the fix, validation would compare against defaults and block the request

    This test should PASS with the fix and FAIL without the fix.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload exactly like frontend sends (existing settings + language change)
    settings_payload = create_frontend_style_payload(existing_settings, language='es')

    # Verify the payload includes existing LLM settings (this is what caused the bug)
    assert 'agent' in settings_payload
    assert 'llm_model' in settings_payload
    assert 'confirmation_mode' in settings_payload
    assert settings_payload['agent'] == 'CodeActAgent'  # Existing LLM setting
    assert settings_payload['llm_model'] == 'openhands/claude-sonnet-4-20250514'  # Existing LLM setting
    assert settings_payload['language'] == 'es'  # The actual change

    response = client.post('/api/settings', json=settings_payload)

    # This should succeed with the fix - user is only changing language, not LLM settings
    assert response.status_code == 200, (
        f'Non-pro user should be able to change language even with existing LLM settings. '
        f'Got: {response.status_code} - {response.json()}'
    )


@pytest.mark.asyncio
async def test_non_pro_can_change_multiple_non_llm_settings_with_existing_llm_settings_bug_fix(
    test_client_non_pro_with_frontend_defaults,
):
    """
    BUG FIX TEST: Non-pro user should be able to change multiple non-LLM settings.

    This test verifies the fix works for multiple non-LLM setting changes.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload with multiple non-LLM changes
    settings_payload = create_frontend_style_payload(
        existing_settings,
        language='fr',  # Changed
        max_iterations=100,  # Changed
        user_consents_to_analytics=True,  # Changed
        enable_sound_notifications=True,  # Changed
        git_user_name='new-user',  # Changed
    )

    # Verify the payload includes existing LLM settings
    assert 'agent' in settings_payload
    assert 'llm_model' in settings_payload
    assert settings_payload['agent'] == 'CodeActAgent'  # Unchanged LLM setting

    response = client.post('/api/settings', json=settings_payload)

    # This should succeed with the fix
    assert response.status_code == 200, (
        f'Non-pro user should be able to change multiple non-LLM settings. '
        f'Got: {response.status_code} - {response.json()}'
    )


@pytest.mark.asyncio
async def test_non_pro_still_blocked_when_actually_changing_llm_settings(
    test_client_non_pro_with_frontend_defaults,
):
    """
    SECURITY TEST: Non-pro user should still be blocked when actually changing LLM settings.

    This test ensures the fix doesn't break the security - users should still be blocked
    when they actually try to change LLM settings.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload that actually changes an LLM setting
    settings_payload = create_frontend_style_payload(
        existing_settings,
        language='fr',  # Non-LLM change (should be allowed)
        llm_model='openai/gpt-4o',  # LLM change (should be blocked)
    )

    response = client.post('/api/settings', json=settings_payload)

    # This should still fail - user is trying to change LLM model
    assert response.status_code == 403, (
        f'Non-pro user should still be blocked when changing LLM settings. '
        f'Got: {response.status_code} - {response.json()}'
    )
    response_data = response.json()
    assert any(
        keyword in response_data.get('detail', '').lower()
        or keyword in response_data.get('error', '').lower()
        for keyword in ['subscription', 'pro', 'upgrade']
    )


@pytest.mark.asyncio
async def test_non_pro_blocked_when_changing_confirmation_mode(
    test_client_non_pro_with_frontend_defaults,
):
    """
    SECURITY TEST: Non-pro user should be blocked when changing confirmation_mode.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload that changes confirmation_mode
    settings_payload = create_frontend_style_payload(
        existing_settings,
        confirmation_mode=True,  # Changed from False to True
    )

    response = client.post('/api/settings', json=settings_payload)

    # This should fail - user is trying to change confirmation_mode (LLM setting)
    assert response.status_code == 403, (
        f'Non-pro user should be blocked when changing confirmation_mode. '
        f'Got: {response.status_code} - {response.json()}'
    )


@pytest.mark.asyncio
async def test_non_pro_blocked_when_changing_agent(
    test_client_non_pro_with_frontend_defaults,
):
    """
    SECURITY TEST: Non-pro user should be blocked when changing agent.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload that changes agent
    settings_payload = create_frontend_style_payload(
        existing_settings,
        agent='PlannerAgent',  # Changed from CodeActAgent
    )

    response = client.post('/api/settings', json=settings_payload)

    # This should fail - user is trying to change agent (LLM setting)
    assert response.status_code == 403, (
        f'Non-pro user should be blocked when changing agent. '
        f'Got: {response.status_code} - {response.json()}'
    )


@pytest.mark.asyncio
async def test_non_pro_blocked_when_changing_search_api_key(
    test_client_non_pro_with_frontend_defaults,
):
    """
    SECURITY TEST: Non-pro user should be blocked when changing search_api_key.
    """
    client, existing_settings = test_client_non_pro_with_frontend_defaults

    # Create payload that changes search_api_key
    settings_payload = create_frontend_style_payload(
        existing_settings,
        search_api_key='new-search-key',  # Changed from empty string
    )

    response = client.post('/api/settings', json=settings_payload)

    # This should fail - user is trying to change search_api_key (LLM setting)
    assert response.status_code == 403, (
        f'Non-pro user should be blocked when changing search_api_key. '
        f'Got: {response.status_code} - {response.json()}'
    )