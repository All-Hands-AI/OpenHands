"""Tests for the start conversation endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.integrations.service_types import ProviderType
from openhands.server.routes.manage_conversations import StartConversationRequest
from openhands.server.services.conversation_service import (
    create_provider_tokens_object,
    setup_init_convo_settings,
)


class TestStartConversationEndpoint:
    """Test the start conversation endpoint functionality."""

    def test_start_conversation_request_model(self):
        """Test that StartConversationRequest model works correctly."""
        # Test with providers
        request = StartConversationRequest(
            providers_set=[ProviderType.GITHUB, ProviderType.GITLAB]
        )
        assert request.providers_set == [ProviderType.GITHUB, ProviderType.GITLAB]

        # Test with empty providers
        request = StartConversationRequest(providers_set=[])
        assert request.providers_set == []

        # Test with None (should default to empty list)
        request = StartConversationRequest()
        assert request.providers_set == []

    @pytest.mark.asyncio
    async def test_setup_init_convo_settings_import(self):
        """Test that setup_init_convo_settings can be imported and called."""

        # Mock the dependencies
        with (
            patch(
                'openhands.server.conversation_utils.conversation_init.SettingsStoreImpl'
            ) as mock_settings_store,
            patch(
                'openhands.server.conversation_utils.conversation_init.SecretsStoreImpl'
            ) as mock_secrets_store,
            patch(
                'openhands.server.conversation_utils.conversation_init.ExperimentManagerImpl'
            ) as mock_experiment_manager,
        ):
            # Setup mocks
            mock_settings = MagicMock()
            mock_settings.__dict__ = {'model': 'test', 'api_key': 'test'}
            mock_settings_instance = AsyncMock()
            mock_settings_instance.load.return_value = mock_settings
            mock_settings_store.get_instance.return_value = mock_settings_instance

            mock_secrets_instance = AsyncMock()
            mock_secrets_instance.load.return_value = None
            mock_secrets_store.get_instance.return_value = mock_secrets_instance

            mock_experiment_manager.run_conversation_variant_test.return_value = (
                MagicMock()
            )

            # Test the function
            result = await setup_init_convo_settings(
                user_id='test_user',
                conversation_id='test_conversation',
                providers_set=[ProviderType.GITHUB],
            )

            # Verify it returns something
            assert result is not None

            # Verify the stores were called
            mock_settings_store.get_instance.assert_called_once()
            mock_secrets_store.get_instance.assert_called_once()
            mock_experiment_manager.run_conversation_variant_test.assert_called_once()

    def test_create_provider_tokens_object(self):
        """Test the create_provider_tokens_object function."""
        # Test with providers
        providers = [ProviderType.GITHUB, ProviderType.GITLAB]
        result = create_provider_tokens_object(providers)

        assert len(result) == 2
        assert ProviderType.GITHUB in result
        assert ProviderType.GITLAB in result

        # Test with empty providers
        result = create_provider_tokens_object([])
        assert len(result) == 0
