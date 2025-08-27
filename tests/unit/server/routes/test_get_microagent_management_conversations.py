from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.integrations.provider import ProviderHandler
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.routes.manage_conversations import (
    get_microagent_management_conversations,
)
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import (
    ConversationMetadata,
    ConversationTrigger,
)


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_success():
    """Test successful retrieval of microagent management conversations."""
    # Mock data
    page_id = 'test_page_123'
    limit = 10
    selected_repository = 'owner/repo'

    # Create mock conversations
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['123'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
        ConversationMetadata(
            conversation_id='conv_2',
            user_id='user_2',
            title='Test Conversation 2',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['456'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id='next_page_456')
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)
    mock_provider_handler.is_pr_open = AsyncMock(return_value=True)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[], next_page_id='next_page_456'
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400  # 24 hours

        # Call the function with correct parameter order
        result = await get_microagent_management_conversations(
            selected_repository=selected_repository,
            page_id=page_id,
            limit=limit,
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify the result
        assert isinstance(result, ConversationInfoResultSet)
        assert result.next_page_id == 'next_page_456'

        # Verify conversation store was called correctly
        mock_conversation_store.search.assert_called_once_with(page_id, limit)

        # Verify provider handler was created with correct tokens
        mock_provider_handler.is_pr_open.assert_called()


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_no_results():
    """Test when no conversations match the criteria."""
    # Mock conversation store with empty results
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=[], next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    with (
        patch('openhands.server.routes.manage_conversations.ProviderHandler'),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function with required selected_repository parameter
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify the result
        assert isinstance(result, ConversationInfoResultSet)
        assert result.next_page_id is None
        assert len(result.results) == 0


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_filter_by_repository():
    """Test filtering conversations by selected repository."""
    # Create mock conversations with different repositories
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository='owner/repo1',
            git_provider='github',
            pr_number=['123'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
        ConversationMetadata(
            conversation_id='conv_2',
            user_id='user_2',
            title='Test Conversation 2',
            selected_repository='owner/repo2',
            git_provider='github',
            pr_number=['456'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)
    mock_provider_handler.is_pr_open = AsyncMock(return_value=True)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function - only repo1 should be included
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[mock_conversations[0]], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function with repository filter
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo1',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify only conversations from the specified repository are returned
        assert len(result.results) == 1
        assert result.results[0].conversation_id == 'conv_1'
        assert result.results[0].selected_repository == 'owner/repo1'


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_filter_by_trigger():
    """Test that only microagent_management conversations are returned."""
    # Create mock conversations with different triggers
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['123'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
        ConversationMetadata(
            conversation_id='conv_2',
            user_id='user_2',
            title='Test Conversation 2',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['456'],
            trigger=ConversationTrigger.GUI,  # Different trigger
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)
    mock_provider_handler.is_pr_open = AsyncMock(return_value=True)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function - only microagent_management should be included
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[mock_conversations[0]], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify only microagent_management conversations are returned
        assert len(result.results) == 1
        assert result.results[0].conversation_id == 'conv_1'
        assert result.results[0].trigger == ConversationTrigger.MICROAGENT_MANAGEMENT


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_filter_inactive_pr():
    """Test filtering out conversations with inactive PRs."""
    # Create mock conversations
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['123'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
        ConversationMetadata(
            conversation_id='conv_2',
            user_id='user_2',
            title='Test Conversation 2',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=['456'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler with one active and one inactive PR
    mock_provider_handler = MagicMock(spec=ProviderHandler)
    mock_provider_handler.is_pr_open = AsyncMock(side_effect=[True, False])

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function - only active PR should be included
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[mock_conversations[0]], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify only conversations with active PRs are returned
        assert len(result.results) == 1
        assert result.results[0].conversation_id == 'conv_1'

        # Verify provider handler was called for both PRs
        assert mock_provider_handler.is_pr_open.call_count == 2


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_no_pr_number():
    """Test conversations without PR numbers are included."""
    # Create mock conversations without PR numbers
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository='owner/repo',
            git_provider='github',
            pr_number=[],  # No PR number
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function
        mock_build_result.return_value = ConversationInfoResultSet(
            results=mock_conversations, next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify conversation without PR number is included
        assert len(result.results) == 1
        assert result.results[0].conversation_id == 'conv_1'

        # Verify provider handler was not called (no PR to check)
        mock_provider_handler.is_pr_open.assert_not_called()


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_no_repository():
    """Test conversations without selected repository are filtered out for PR checks."""
    # Create mock conversations without repository
    mock_conversations = [
        ConversationMetadata(
            conversation_id='conv_1',
            user_id='user_1',
            title='Test Conversation 1',
            selected_repository=None,  # No repository
            git_provider='github',
            pr_number=['123'],
            trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
            created_at=datetime.now(timezone.utc),
            last_updated_at=datetime.now(timezone.utc),
        ),
    ]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function - conversation should be filtered out due to repository mismatch
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify conversation without repository is filtered out
        assert len(result.results) == 0

        # Verify provider handler was not called (no repository for PR check)
        mock_provider_handler.is_pr_open.assert_not_called()


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_age_filter():
    """Test that conversations are filtered by age."""
    # Create mock conversations with different ages
    now = datetime.now(timezone.utc)
    old_conversation = ConversationMetadata(
        conversation_id='conv_old',
        user_id='user_1',
        title='Old Conversation',
        selected_repository='owner/repo',
        git_provider='github',
        pr_number=['123'],
        trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
        created_at=now.replace(year=now.year - 1),  # Very old
        last_updated_at=now.replace(year=now.year - 1),
    )

    recent_conversation = ConversationMetadata(
        conversation_id='conv_recent',
        user_id='user_2',
        title='Recent Conversation',
        selected_repository='owner/repo',
        git_provider='github',
        pr_number=['456'],
        trigger=ConversationTrigger.MICROAGENT_MANAGEMENT,
        created_at=now,  # Recent
        last_updated_at=now,
    )

    mock_conversations = [old_conversation, recent_conversation]

    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=mock_conversations, next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    # Mock provider handler
    mock_provider_handler = MagicMock(spec=ProviderHandler)
    mock_provider_handler.is_pr_open = AsyncMock(return_value=True)

    with (
        patch(
            'openhands.server.routes.manage_conversations.ProviderHandler',
            return_value=mock_provider_handler,
        ),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function - only recent conversation should be included
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[recent_conversation], next_page_id=None
        )

        # Mock config with short max age
        mock_config.conversation_max_age_seconds = 3600  # 1 hour

        # Call the function
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify only recent conversation is returned
        assert len(result.results) == 1
        assert result.results[0].conversation_id == 'conv_recent'


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_pagination():
    """Test pagination functionality."""
    # Mock conversation store with pagination
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=[], next_page_id='next_page_789')
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    with (
        patch('openhands.server.routes.manage_conversations.ProviderHandler'),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[], next_page_id='next_page_789'
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function with pagination parameters
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            page_id='test_page',
            limit=5,
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify pagination parameters were passed correctly
        mock_conversation_store.search.assert_called_once_with('test_page', 5)
        assert result.next_page_id == 'next_page_789'


@pytest.mark.asyncio
async def test_get_microagent_management_conversations_default_parameters():
    """Test default parameter values."""
    # Mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.search = AsyncMock(
        return_value=MagicMock(results=[], next_page_id=None)
    )

    # Mock provider tokens
    mock_provider_tokens = {'github': 'token_123'}

    with (
        patch('openhands.server.routes.manage_conversations.ProviderHandler'),
        patch(
            'openhands.server.routes.manage_conversations._build_conversation_result_set'
        ) as mock_build_result,
        patch('openhands.server.routes.manage_conversations.config') as mock_config,
    ):
        # Mock the build result function
        mock_build_result.return_value = ConversationInfoResultSet(
            results=[], next_page_id=None
        )

        # Mock config
        mock_config.conversation_max_age_seconds = 86400

        # Call the function without parameters (selected_repository is required)
        result = await get_microagent_management_conversations(
            selected_repository='owner/repo',
            conversation_store=mock_conversation_store,
            provider_tokens=mock_provider_tokens,
        )

        # Verify default values were used
        mock_conversation_store.search.assert_called_once_with(None, 20)
        assert isinstance(result, ConversationInfoResultSet)
