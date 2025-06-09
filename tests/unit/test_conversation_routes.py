import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.responses import JSONResponse

from openhands.microagent.microagent import KnowledgeMicroagent, RepoMicroagent
from openhands.microagent.types import MicroagentMetadata, MicroagentType
from openhands.server.routes.conversation import get_microagents
from openhands.server.session.conversation import ServerConversation


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
