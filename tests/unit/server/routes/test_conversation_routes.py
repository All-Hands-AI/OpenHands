import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.responses import JSONResponse

from openhands.microagent.microagent import KnowledgeMicroagent, RepoMicroagent
from openhands.microagent.types import MicroagentMetadata, MicroagentType
from openhands.server.routes.conversation import get_microagents
from openhands.server.routes.manage_conversations import (
    UpdateConversationRequest,
    update_conversation,
)
from openhands.server.session.conversation import ServerConversation
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata


@pytest.mark.asyncio
async def test_get_microagents():
    """Test the get_microagents function directly."""
    # Create mock microagents
    from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig

    repo_microagent = RepoMicroagent(
        name='test_repo',
        content='This is a test repo microagent',
        metadata=MicroagentMetadata(
            name='test_repo',
            type=MicroagentType.REPO_KNOWLEDGE,
            inputs=[],  # Empty inputs to match the expected behavior
            mcp_tools=MCPConfig(
                stdio_servers=[
                    MCPStdioServerConfig(name='git', command='git'),
                    MCPStdioServerConfig(name='file_editor', command='editor'),
                ]
            ),
        ),
        source='test_source',
        type=MicroagentType.REPO_KNOWLEDGE,
    )

    knowledge_microagent = KnowledgeMicroagent(
        name='test_knowledge',
        content='This is a test knowledge microagent',
        metadata=MicroagentMetadata(
            name='test_knowledge',
            type=MicroagentType.KNOWLEDGE,
            triggers=['test', 'knowledge'],
            inputs=[],  # Empty inputs to match the expected behavior
            mcp_tools=MCPConfig(
                stdio_servers=[
                    MCPStdioServerConfig(name='search', command='search'),
                    MCPStdioServerConfig(name='fetch', command='fetch'),
                ]
            ),
        ),
        source='test_source',
        type=MicroagentType.KNOWLEDGE,
    )

    # Mock the agent session and memory
    mock_memory = MagicMock()
    mock_memory.repo_microagents = {'test_repo': repo_microagent}
    mock_memory.knowledge_microagents = {'test_knowledge': knowledge_microagent}

    mock_agent_session = MagicMock()
    mock_agent_session.memory = mock_memory

    # Create a mock ServerConversation
    mock_conversation = MagicMock(spec=ServerConversation)
    mock_conversation.sid = 'test_sid'

    # Mock the conversation manager
    with patch(
        'openhands.server.routes.conversation.conversation_manager'
    ) as mock_manager:
        # Set up the mocks
        mock_manager.get_agent_session.return_value = mock_agent_session

        # Call the function directly
        response = await get_microagents(conversation=mock_conversation)

        # Verify the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

        # Parse the JSON content
        content = json.loads(response.body)
        assert 'microagents' in content
        assert len(content['microagents']) == 2

        # Check repo microagent
        repo_agent = next(m for m in content['microagents'] if m['name'] == 'test_repo')
        assert repo_agent['type'] == 'repo'
        assert repo_agent['content'] == 'This is a test repo microagent'
        assert repo_agent['triggers'] == []
        assert repo_agent['inputs'] == []  # Expect empty inputs
        assert repo_agent['tools'] == ['git', 'file_editor']

        # Check knowledge microagent
        knowledge_agent = next(
            m for m in content['microagents'] if m['name'] == 'test_knowledge'
        )
        assert knowledge_agent['type'] == 'knowledge'
        assert knowledge_agent['content'] == 'This is a test knowledge microagent'
        assert knowledge_agent['triggers'] == ['test', 'knowledge']
        assert knowledge_agent['inputs'] == []  # Expect empty inputs
        assert knowledge_agent['tools'] == ['search', 'fetch']


@pytest.mark.asyncio
async def test_get_microagents_no_agent_session():
    """Test the get_microagents function when no agent session is found."""
    # Create a mock ServerConversation
    mock_conversation = MagicMock(spec=ServerConversation)
    mock_conversation.sid = 'test_sid'

    # Mock the conversation manager
    with patch(
        'openhands.server.routes.conversation.conversation_manager'
    ) as mock_manager:
        # Set up the mocks
        mock_manager.get_agent_session.return_value = None

        # Call the function directly
        response = await get_microagents(conversation=mock_conversation)

        # Verify the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

        # Parse the JSON content
        content = json.loads(response.body)
        assert 'error' in content
        assert 'Agent session not found' in content['error']


@pytest.mark.asyncio
async def test_get_microagents_exception():
    """Test the get_microagents function when an exception occurs."""
    # Create a mock ServerConversation
    mock_conversation = MagicMock(spec=ServerConversation)
    mock_conversation.sid = 'test_sid'

    # Mock the conversation manager
    with patch(
        'openhands.server.routes.conversation.conversation_manager'
    ) as mock_manager:
        # Set up the mocks to raise an exception
        mock_manager.get_agent_session.side_effect = Exception('Test exception')

        # Call the function directly
        response = await get_microagents(conversation=mock_conversation)

        # Verify the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # Parse the JSON content
        content = json.loads(response.body)
        assert 'error' in content
        assert 'Test exception' in content['error']


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_success():
    """Test successful conversation update."""
    # Mock data
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    original_title = 'Original Title'
    new_title = 'Updated Title'

    # Create mock metadata
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=user_id,
        title=original_title,
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request
    update_request = UpdateConversationRequest(title=new_title)

    # Mock the conversation manager socket
    mock_sio = AsyncMock()

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify the result
        assert result is True

        # Verify metadata was fetched
        mock_conversation_store.get_metadata.assert_called_once_with(conversation_id)

        # Verify metadata was updated and saved
        mock_conversation_store.save_metadata.assert_called_once()
        saved_metadata = mock_conversation_store.save_metadata.call_args[0][0]
        assert saved_metadata.title == new_title.strip()
        assert saved_metadata.last_updated_at is not None

        # Verify socket emission
        mock_sio.emit.assert_called_once()
        emit_call = mock_sio.emit.call_args
        assert emit_call[0][0] == 'oh_event'
        assert emit_call[0][1]['conversation_title'] == new_title
        assert emit_call[1]['to'] == f'room:{conversation_id}'


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_not_found():
    """Test conversation update when conversation doesn't exist."""
    conversation_id = 'nonexistent_conversation'
    user_id = 'test_user_456'

    # Create mock conversation store that raises FileNotFoundError
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(side_effect=FileNotFoundError())

    # Create update request
    update_request = UpdateConversationRequest(title='New Title')

    # Call the function
    result = await update_conversation(
        conversation_id=conversation_id,
        data=update_request,
        user_id=user_id,
        conversation_store=mock_conversation_store,
    )

    # Verify the result is a 404 error response
    assert isinstance(result, JSONResponse)
    assert result.status_code == status.HTTP_404_NOT_FOUND

    # Parse the JSON content
    content = json.loads(result.body)
    assert content['status'] == 'error'
    assert content['message'] == 'Conversation not found'
    assert content['msg_id'] == 'CONVERSATION$NOT_FOUND'


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_permission_denied():
    """Test conversation update when user doesn't own the conversation."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    owner_id = 'different_user_789'

    # Create mock metadata owned by different user
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=owner_id,
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)

    # Create update request
    update_request = UpdateConversationRequest(title='New Title')

    # Call the function
    result = await update_conversation(
        conversation_id=conversation_id,
        data=update_request,
        user_id=user_id,
        conversation_store=mock_conversation_store,
    )

    # Verify the result is a 403 error response
    assert isinstance(result, JSONResponse)
    assert result.status_code == status.HTTP_403_FORBIDDEN

    # Parse the JSON content
    content = json.loads(result.body)
    assert content['status'] == 'error'
    assert (
        content['message']
        == 'Permission denied: You can only update your own conversations'
    )
    assert content['msg_id'] == 'AUTHORIZATION$PERMISSION_DENIED'


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_permission_denied_no_user_id():
    """Test conversation update when user_id is None and metadata has user_id."""
    conversation_id = 'test_conversation_123'
    user_id = None
    owner_id = 'some_user_789'

    # Create mock metadata owned by a user
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=owner_id,
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)

    # Create update request
    update_request = UpdateConversationRequest(title='New Title')

    # Call the function
    result = await update_conversation(
        conversation_id=conversation_id,
        data=update_request,
        user_id=user_id,
        conversation_store=mock_conversation_store,
    )

    # Verify the result is successful (current logic allows this)
    assert result is True


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_socket_emission_error():
    """Test conversation update when socket emission fails."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    new_title = 'Updated Title'

    # Create mock metadata
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=user_id,
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request
    update_request = UpdateConversationRequest(title=new_title)

    # Mock the conversation manager socket to raise an exception
    mock_sio = AsyncMock()
    mock_sio.emit.side_effect = Exception('Socket error')

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function (should still succeed despite socket error)
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify the result is still successful
        assert result is True

        # Verify metadata was still saved
        mock_conversation_store.save_metadata.assert_called_once()


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_general_exception():
    """Test conversation update when an unexpected exception occurs."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'

    # Create mock conversation store that raises a general exception
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(
        side_effect=Exception('Database error')
    )

    # Create update request
    update_request = UpdateConversationRequest(title='New Title')

    # Call the function
    result = await update_conversation(
        conversation_id=conversation_id,
        data=update_request,
        user_id=user_id,
        conversation_store=mock_conversation_store,
    )

    # Verify the result is a 500 error response
    assert isinstance(result, JSONResponse)
    assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Parse the JSON content
    content = json.loads(result.body)
    assert content['status'] == 'error'
    assert 'Failed to update conversation' in content['message']
    assert content['msg_id'] == 'CONVERSATION$UPDATE_ERROR'


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_title_whitespace_trimming():
    """Test that conversation title is properly trimmed of whitespace."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    title_with_whitespace = '  Trimmed Title  '
    expected_title = 'Trimmed Title'

    # Create mock metadata
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=user_id,
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request with whitespace
    update_request = UpdateConversationRequest(title=title_with_whitespace)

    # Mock the conversation manager socket
    mock_sio = AsyncMock()

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify the result
        assert result is True

        # Verify metadata was updated with trimmed title
        mock_conversation_store.save_metadata.assert_called_once()
        saved_metadata = mock_conversation_store.save_metadata.call_args[0][0]
        assert saved_metadata.title == expected_title


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_user_owns_conversation():
    """Test successful update when user owns the conversation."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    new_title = 'Updated Title'

    # Create mock metadata owned by the same user
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=user_id,  # Same user
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request
    update_request = UpdateConversationRequest(title=new_title)

    # Mock the conversation manager socket
    mock_sio = AsyncMock()

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify success
        assert result is True
        mock_conversation_store.save_metadata.assert_called_once()


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_last_updated_at_set():
    """Test that last_updated_at is properly set when updating."""
    conversation_id = 'test_conversation_123'
    user_id = 'test_user_456'
    new_title = 'Updated Title'

    # Create mock metadata
    original_timestamp = datetime.now(timezone.utc)
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=user_id,
        title='Original Title',
        selected_repository=None,
        last_updated_at=original_timestamp,
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request
    update_request = UpdateConversationRequest(title=new_title)

    # Mock the conversation manager socket
    mock_sio = AsyncMock()

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify success
        assert result is True

        # Verify last_updated_at was updated
        mock_conversation_store.save_metadata.assert_called_once()
        saved_metadata = mock_conversation_store.save_metadata.call_args[0][0]
        assert saved_metadata.last_updated_at > original_timestamp


@pytest.mark.update_conversation
@pytest.mark.asyncio
async def test_update_conversation_no_user_id_no_metadata_user_id():
    """Test successful update when both user_id and metadata.user_id are None."""
    conversation_id = 'test_conversation_123'
    user_id = None
    new_title = 'Updated Title'

    # Create mock metadata with no user_id
    mock_metadata = ConversationMetadata(
        conversation_id=conversation_id,
        user_id=None,
        title='Original Title',
        selected_repository=None,
        last_updated_at=datetime.now(timezone.utc),
    )

    # Create mock conversation store
    mock_conversation_store = MagicMock(spec=ConversationStore)
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create update request
    update_request = UpdateConversationRequest(title=new_title)

    # Mock the conversation manager socket
    mock_sio = AsyncMock()

    with patch(
        'openhands.server.routes.manage_conversations.conversation_manager'
    ) as mock_manager:
        mock_manager.sio = mock_sio

        # Call the function
        result = await update_conversation(
            conversation_id=conversation_id,
            data=update_request,
            user_id=user_id,
            conversation_store=mock_conversation_store,
        )

        # Verify success (should work when both are None)
        assert result is True
        mock_conversation_store.save_metadata.assert_called_once()
