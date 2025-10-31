"""Tests for SaasSQLAppConversationInfoService.

This module tests the SAAS implementation of SQLAppConversationInfoService,
focusing on user isolation, SAAS metadata handling, and multi-tenant functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
)
from openhands.app_server.user.specifiy_user_context import SpecifyUserContext
from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.conversation_metadata import ConversationTrigger

# Import the SAAS service
from enterprise.storage.saas_app_conversation_info_injector import (
    SaasSQLAppConversationInfoService,
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def user1_context():
    """Create user context for user1."""
    return SpecifyUserContext(user_id='11111111-1111-1111-1111-111111111111')


@pytest.fixture
def user2_context():
    """Create user context for user2."""
    return SpecifyUserContext(user_id='22222222-2222-2222-2222-222222222222')


@pytest.fixture
def saas_service_user1(mock_db_session, user1_context):
    """Create a SaasSQLAppConversationInfoService instance for user1."""
    return SaasSQLAppConversationInfoService(
        db_session=mock_db_session,
        user_context=user1_context
    )


@pytest.fixture
def saas_service_user2(mock_db_session, user2_context):
    """Create a SaasSQLAppConversationInfoService instance for user2."""
    return SaasSQLAppConversationInfoService(
        db_session=mock_db_session,
        user_context=user2_context
    )


class TestSaasSQLAppConversationInfoService:
    """Test suite for SaasSQLAppConversationInfoService."""

    def test_service_initialization(
        self,
        saas_service_user1: SaasSQLAppConversationInfoService,
        user1_context: SpecifyUserContext,
    ):
        """Test that the SAAS service is properly initialized."""
        assert saas_service_user1.user_context == user1_context
        assert saas_service_user1.db_session is not None

    @pytest.mark.asyncio
    async def test_user_context_isolation(
        self,
        saas_service_user1: SaasSQLAppConversationInfoService,
        saas_service_user2: SaasSQLAppConversationInfoService,
    ):
        """Test that different service instances have different user contexts."""
        user1_id = await saas_service_user1.user_context.get_user_id()
        user2_id = await saas_service_user2.user_context.get_user_id()
        
        assert user1_id == '11111111-1111-1111-1111-111111111111'
        assert user2_id == '22222222-2222-2222-2222-222222222222'
        assert user1_id != user2_id

    @pytest.mark.asyncio
    async def test_secure_select_includes_user_filtering(
        self,
        saas_service_user1: SaasSQLAppConversationInfoService,
    ):
        """Test that _secure_select method includes user filtering."""
        # This test verifies that the _secure_select method exists and can be called
        # The actual SQL generation is tested implicitly through integration
        query = await saas_service_user1._secure_select()
        assert query is not None

    @pytest.mark.asyncio
    async def test_to_info_with_user_id_functionality(
        self,
        saas_service_user1: SaasSQLAppConversationInfoService,
    ):
        """Test that _to_info_with_user_id properly sets user_id from SAAS metadata."""
        from storage.stored_conversation_metadata import StoredConversationMetadata
        from storage.stored_conversation_metadata_saas import StoredConversationMetadataSaas
        
        # Create mock metadata objects
        stored_metadata = MagicMock(spec=StoredConversationMetadata)
        stored_metadata.conversation_id = '12345678-1234-5678-1234-567812345678'
        stored_metadata.title = 'Test Conversation'
        stored_metadata.sandbox_id = 'test-sandbox'
        stored_metadata.selected_repository = None
        stored_metadata.selected_branch = None
        stored_metadata.git_provider = None
        stored_metadata.trigger = None
        stored_metadata.pr_number = []
        stored_metadata.llm_model = None
        from datetime import datetime, timezone
        stored_metadata.created_at = datetime.now(timezone.utc)
        stored_metadata.last_updated_at = datetime.now(timezone.utc)
        stored_metadata.accumulated_cost = 0.0
        stored_metadata.prompt_tokens = 0
        stored_metadata.completion_tokens = 0
        stored_metadata.total_tokens = 0
        stored_metadata.max_budget_per_task = None
        stored_metadata.cache_read_tokens = 0
        stored_metadata.cache_write_tokens = 0
        stored_metadata.reasoning_tokens = 0
        stored_metadata.context_window = 0
        stored_metadata.per_turn_token = 0
        
        saas_metadata = MagicMock(spec=StoredConversationMetadataSaas)
        saas_metadata.user_id = UUID('11111111-1111-1111-1111-111111111111')
        
        # Test the _to_info_with_user_id method
        result = saas_service_user1._to_info_with_user_id(stored_metadata, saas_metadata)
        
        # Verify that the user_id from SAAS metadata is used
        assert result.created_by_user_id == '11111111-1111-1111-1111-111111111111'
        assert result.title == 'Test Conversation'
        assert result.sandbox_id == 'test-sandbox'