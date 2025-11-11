"""Tests for /start endpoint provider token handling."""

from types import MappingProxyType
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.server.data_models.agent_loop_info import AgentLoopInfo
from openhands.server.routes.manage_conversations import (
    ProvidersSetModel,
    start_conversation,
)
from openhands.server.types import AppMode
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.data_models.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a real Settings object with minimal required fields."""
    return Settings(
        language='en',
        agent='CodeActAgent',
        max_iterations=100,
        llm_model='anthropic/claude-3-5-sonnet-20241022',
        llm_api_key=SecretStr('test_api_key_12345'),
        llm_base_url=None,
    )


@pytest.fixture
def mock_provider_tokens():
    """Create real provider tokens to test with."""
    return MappingProxyType(
        {
            ProviderType.GITHUB: ProviderToken(
                token=SecretStr('ghp_real_token_test123'), user_id='test_user_456'
            )
        }
    )


@pytest.fixture
def mock_conversation_metadata():
    """Create a real ConversationMetadata object."""
    return ConversationMetadata(
        conversation_id='test_conv_123',
        user_id='test_user_456',
        title='Test Conversation',
        selected_repository='test/repo',
        selected_branch='main',
        git_provider=ProviderType.GITHUB,
    )


@pytest.mark.asyncio
async def test_start_endpoint_passes_provider_tokens(
    mock_settings, mock_provider_tokens, mock_conversation_metadata
):
    """Test that /start endpoint passes provider_tokens to setup_init_conversation_settings.

    This test verifies the full end-to-end flow with real tokens through to ConversationInitData.
    """
    conversation_id = 'test_conv_123'
    user_id = 'test_user_456'
    providers_set = ProvidersSetModel(providers_set=[ProviderType.GITHUB])

    # Mock conversation store
    mock_conversation_store = AsyncMock()
    mock_conversation_store.get_metadata = AsyncMock(
        return_value=mock_conversation_metadata
    )

    # Mock agent loop info that will be returned
    mock_agent_loop_info = AgentLoopInfo(
        conversation_id=conversation_id,
        url=None,
        session_api_key=None,
        event_store=None,
        status=ConversationStatus.RUNNING,
    )

    # Mock only infrastructure - let setup_init_conversation_settings run for real
    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        # Mock the stores that setup_init_conversation_settings needs
        with patch(
            'openhands.server.services.conversation_service.SettingsStoreImpl.get_instance'
        ) as mock_settings_store_cls:
            with patch(
                'openhands.server.services.conversation_service.SecretsStoreImpl.get_instance'
            ) as mock_secrets_store_cls:
                with patch(
                    'openhands.server.services.conversation_service.server_config'
                ) as mock_server_config:
                    # Setup store mocks
                    mock_settings_store = AsyncMock()
                    mock_settings_store.load = AsyncMock(return_value=mock_settings)
                    mock_settings_store_cls.return_value = mock_settings_store

                    mock_secrets_store = AsyncMock()
                    mock_secrets_store.load = AsyncMock(return_value=None)
                    mock_secrets_store_cls.return_value = mock_secrets_store

                    mock_server_config.app_mode = AppMode.SAAS

                    mock_manager.maybe_start_agent_loop = AsyncMock(
                        return_value=mock_agent_loop_info
                    )

                    # Call endpoint with provider tokens
                    response = await start_conversation(
                        providers_set=providers_set,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        provider_tokens=mock_provider_tokens,
                        settings=mock_settings,
                        conversation_store=mock_conversation_store,
                    )

                    # Verify ConversationInitData has real provider tokens
                    mock_manager.maybe_start_agent_loop.assert_called_once()
                    call_kwargs = mock_manager.maybe_start_agent_loop.call_args[1]
                    conversation_init_data = call_kwargs['settings']

                    assert conversation_init_data.git_provider_tokens is not None
                    assert (
                        conversation_init_data.git_provider_tokens
                        == mock_provider_tokens
                    )
                    assert (
                        ProviderType.GITHUB
                        in conversation_init_data.git_provider_tokens
                    )

                    github_token = conversation_init_data.git_provider_tokens[
                        ProviderType.GITHUB
                    ]
                    assert (
                        github_token.token.get_secret_value()
                        == 'ghp_real_token_test123'
                    )
                    assert github_token.user_id == 'test_user_456'

                    assert response.status == 'ok'
                    assert response.conversation_id == conversation_id
