from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from openhands.core.schema.action import ActionType
from openhands.events.action.message import MessageAction
from openhands.events.observation.commands import CmdOutputObservation
from openhands.server.app import app
from openhands.server.routes.manage_conversations import InitSessionRequest
from openhands.storage.data_models.conversation_status import ConversationStatus


class MockConversation:
    def __init__(self, conversation_id: str, user_id: str, final_result: str = None):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.final_result = final_result


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_conversation_metadata():
    return {
        'conversation_id': 'test-conversation-id',
        'title': 'Test Conversation',
        'last_updated_at': datetime.fromisoformat('2025-01-01T00:01:00+00:00').replace(
            tzinfo=timezone.utc
        ),
        'created_at': datetime.fromisoformat('2025-01-01T00:00:00+00:00').replace(
            tzinfo=timezone.utc
        ),
        'selected_repository': 'test/repo',
    }


@pytest.fixture
def mock_events():
    """Create mock events for testing event processing."""
    # Create events with proper constructors
    events = [
        MessageAction(content='Hello, how can I help?'),
        CmdOutputObservation(content='ls -la\nfile1.txt\nfile2.py', command='ls -la'),
        MessageAction(content='Show me files'),
    ]
    # Set sources after creation using the private attribute
    from openhands.events.event import EventSource

    events[0]._source = EventSource.AGENT
    events[1]._source = EventSource.AGENT
    events[2]._source = EventSource.USER
    return events


class TestIntegrationConversationAPI:
    """Test cases for the integration conversation API endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, test_client):
        """Test successful conversation creation."""
        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation:
            # Mock to return FastAPI JSONResponse
            from fastapi.responses import JSONResponse

            mock_new_conversation.return_value = JSONResponse(
                content={'status': 'ok', 'conversation_id': 'test-conversation-id'}
            )

            # Use the new integration request format
            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'research_mode': 'normal',
                'space_id': 123,
                'thread_follow_up': None,
                'followup_discover_id': None,
                'space_section_id': 456,
            }

            # Mock authentication middleware
            with patch(
                'openhands.server.middleware.JWTAuthMiddleware.dispatch'
            ) as mock_auth:

                async def mock_auth_dispatch(request, call_next):
                    # Simulate authenticated request
                    request.state.user_id = 'test-user-id'
                    request.state.user = type(
                        'User', (), {'mnemonic': 'test-mnemonic'}
                    )()
                    return await call_next(request)

                mock_auth.side_effect = mock_auth_dispatch

                response = test_client.post(
                    '/api/v1/integration/conversations/',
                    json=payload,
                    headers={'Authorization': 'Bearer test-token'},
                )

                assert response.status_code == 200
                mock_new_conversation.assert_called_once()

                # Verify the correct InitSessionRequest was passed
                call_args = mock_new_conversation.call_args
                request, data = call_args[0]

                assert isinstance(data, InitSessionRequest)
                assert data.initial_user_msg == 'Hello, I need help with coding'
                # Note: The integration endpoint now accepts different fields and converts to InitSessionRequest

    @pytest.mark.asyncio
    async def test_create_conversation_error(self, test_client):
        """Test conversation creation with error."""
        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation:
            mock_new_conversation.side_effect = HTTPException(
                status_code=400, detail='Missing required settings'
            )

            payload = {'initial_user_msg': 'Hello', 'research_mode': 'normal'}

            response = test_client.post(
                '/api/v1/integration/conversations/',
                json=payload,
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_conversation_success(
        self, test_client, mock_conversation_metadata, mock_events
    ):
        """Test successful conversation retrieval with events."""
        conversation_id = 'test-conversation-id'
        user_id = 'test-user-id'

        # Mock dependencies
        mock_conversation = MockConversation(
            conversation_id, user_id, 'Task completed successfully'
        )

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.get_github_user_id'
        ) as mock_get_github_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module, patch(
            'openhands.server.routes.integration.conversation.ConversationStoreImpl'
        ) as mock_conversation_store, patch(
            'openhands.server.routes.integration.conversation.conversation_manager'
        ) as mock_conversation_manager, patch(
            'openhands.server.routes.integration.conversation.EventStore'
        ) as mock_event_store_cls, patch(
            'openhands.server.routes.integration.conversation.AsyncEventStoreWrapper'
        ) as mock_async_wrapper, patch(
            'openhands.server.routes.integration.conversation.event_to_dict'
        ) as mock_event_to_dict:
            # Setup mocks
            mock_get_user_id.return_value = user_id
            mock_get_github_user_id.return_value = None
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            # Mock conversation store
            mock_store_instance = MagicMock()
            mock_conversation_store.get_instance = AsyncMock(
                return_value=mock_store_instance
            )

            # Mock metadata
            mock_metadata = MagicMock()
            mock_metadata.conversation_id = conversation_id
            mock_metadata.title = 'Test Conversation'
            mock_metadata.last_updated_at = mock_conversation_metadata[
                'last_updated_at'
            ]
            mock_metadata.created_at = mock_conversation_metadata['created_at']
            mock_metadata.selected_repository = 'test/repo'
            mock_store_instance.get_metadata = AsyncMock(return_value=mock_metadata)

            # Mock conversation manager
            mock_conversation_manager.is_agent_loop_running = AsyncMock(
                return_value=False
            )
            mock_conversation_manager.file_store = MagicMock()

            # Mock event store and events
            mock_event_store = MagicMock()
            mock_event_store_cls.return_value = mock_event_store

            # Create mock async event wrapper that yields events
            mock_async_event_store = MagicMock()

            async def mock_async_iter(self):
                for event in mock_events:
                    yield event

            mock_async_event_store.__aiter__ = mock_async_iter
            mock_async_wrapper.return_value = mock_async_event_store

            # Mock event_to_dict to return proper event dictionaries
            def mock_event_to_dict_func(event):
                return {
                    'id': f'event-{id(event)}',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': event.source.value if event.source else 'unknown',
                    'action': event.__class__.__name__,
                    'message': getattr(event, 'content', ''),
                }

            mock_event_to_dict.side_effect = mock_event_to_dict_func

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data['conversation_id'] == conversation_id
            assert data['title'] == 'Test Conversation'
            assert data['status'] == ConversationStatus.FINISHED.value
            assert data['selected_repository'] == 'test/repo'
            assert data['final_result'] == 'Task completed successfully'
            assert 'events' in data
            assert isinstance(data['events'], list)

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, test_client):
        """Test getting a conversation that doesn't exist."""
        conversation_id = 'non-existent-id'

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module:
            mock_get_user_id.return_value = 'test-user-id'
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=None
            )

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 404
            assert response.json()['detail'] == 'Conversation not found'

    @pytest.mark.asyncio
    async def test_get_conversation_store_not_found(self, test_client):
        """Test getting a conversation when store metadata is not found."""
        conversation_id = 'test-conversation-id'
        user_id = 'test-user-id'

        mock_conversation = MockConversation(conversation_id, user_id)

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.get_github_user_id'
        ) as mock_get_github_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module, patch(
            'openhands.server.routes.integration.conversation.ConversationStoreImpl'
        ) as mock_conversation_store:
            mock_get_user_id.return_value = user_id
            mock_get_github_user_id.return_value = None
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            # Mock store to raise FileNotFoundError
            mock_store_instance = MagicMock()
            mock_conversation_store.get_instance = AsyncMock(
                return_value=mock_store_instance
            )
            mock_store_instance.get_metadata = AsyncMock(
                side_effect=FileNotFoundError('Metadata not found')
            )

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 404
            assert response.json()['detail'] == 'Conversation not found'

    @pytest.mark.asyncio
    async def test_get_conversation_with_streaming_events(
        self, test_client, mock_conversation_metadata
    ):
        """Test conversation retrieval with streaming message events."""
        conversation_id = 'test-conversation-id'
        user_id = 'test-user-id'

        mock_conversation = MockConversation(conversation_id, user_id)

        # Create mock streaming events
        streaming_events = [
            MagicMock(
                action=ActionType.STREAMING_MESSAGE, source='agent', message='Hello'
            ),
            MagicMock(
                action=ActionType.STREAMING_MESSAGE, source='agent', message=' world'
            ),
            MagicMock(action=ActionType.STREAMING_MESSAGE, source='agent', message='!'),
        ]

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.get_github_user_id'
        ) as mock_get_github_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module, patch(
            'openhands.server.routes.integration.conversation.ConversationStoreImpl'
        ) as mock_conversation_store, patch(
            'openhands.server.routes.integration.conversation.conversation_manager'
        ) as mock_conversation_manager, patch(
            'openhands.server.routes.integration.conversation.EventStore'
        ) as mock_event_store_cls, patch(
            'openhands.server.routes.integration.conversation.AsyncEventStoreWrapper'
        ) as mock_async_wrapper, patch(
            'openhands.server.routes.integration.conversation.event_to_dict'
        ) as mock_event_to_dict:
            # Setup basic mocks
            mock_get_user_id.return_value = user_id
            mock_get_github_user_id.return_value = None
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            # Mock conversation store
            mock_store_instance = MagicMock()
            mock_conversation_store.get_instance = AsyncMock(
                return_value=mock_store_instance
            )

            mock_metadata = MagicMock()
            mock_metadata.conversation_id = conversation_id
            mock_metadata.title = 'Test Conversation'
            mock_metadata.last_updated_at = mock_conversation_metadata[
                'last_updated_at'
            ]
            mock_metadata.created_at = mock_conversation_metadata['created_at']
            mock_metadata.selected_repository = 'test/repo'
            mock_store_instance.get_metadata = AsyncMock(return_value=mock_metadata)

            mock_conversation_manager.is_agent_loop_running = AsyncMock(
                return_value=False
            )
            mock_conversation_manager.file_store = MagicMock()

            # Mock event store
            mock_event_store = MagicMock()
            mock_event_store_cls.return_value = mock_event_store

            # Mock async event wrapper that yields streaming events
            mock_async_event_store = MagicMock()

            async def mock_async_iter(self):
                for event in streaming_events:
                    yield event

            mock_async_event_store.__aiter__ = mock_async_iter
            mock_async_wrapper.return_value = mock_async_event_store

            # Mock event_to_dict for streaming events
            def mock_event_to_dict_func(event):
                return {
                    'action': event.action,
                    'source': event.source,
                    'message': event.message,
                }

            mock_event_to_dict.side_effect = mock_event_to_dict_func

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            data = response.json()

            # Should have 1 combined streaming message
            assert len(data['events']) == 1
            # The streaming messages should be combined
            combined_message = data['events'][0]
            assert combined_message['message'] == 'Hello world!'

    @pytest.mark.asyncio
    async def test_get_conversation_running_status(
        self, test_client, mock_conversation_metadata
    ):
        """Test conversation retrieval when agent loop is running."""
        conversation_id = 'test-conversation-id'
        user_id = 'test-user-id'

        mock_conversation = MockConversation(conversation_id, user_id)

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.get_github_user_id'
        ) as mock_get_github_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module, patch(
            'openhands.server.routes.integration.conversation.ConversationStoreImpl'
        ) as mock_conversation_store, patch(
            'openhands.server.routes.integration.conversation.conversation_manager'
        ) as mock_conversation_manager, patch(
            'openhands.server.routes.integration.conversation.EventStore'
        ) as mock_event_store_cls, patch(
            'openhands.server.routes.integration.conversation.AsyncEventStoreWrapper'
        ) as mock_async_wrapper:
            # Setup basic mocks
            mock_get_user_id.return_value = user_id
            mock_get_github_user_id.return_value = None
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            # Mock conversation store
            mock_store_instance = MagicMock()
            mock_conversation_store.get_instance = AsyncMock(
                return_value=mock_store_instance
            )

            mock_metadata = MagicMock()
            mock_metadata.conversation_id = conversation_id
            mock_metadata.title = 'Running Conversation'
            mock_metadata.last_updated_at = mock_conversation_metadata[
                'last_updated_at'
            ]
            mock_metadata.created_at = mock_conversation_metadata['created_at']
            mock_metadata.selected_repository = 'test/repo'
            mock_store_instance.get_metadata = AsyncMock(return_value=mock_metadata)

            # Mock conversation manager to return running status
            mock_conversation_manager.is_agent_loop_running = AsyncMock(
                return_value=True
            )
            mock_conversation_manager.file_store = MagicMock()

            # Mock empty event store
            mock_event_store = MagicMock()
            mock_event_store_cls.return_value = mock_event_store

            mock_async_event_store = MagicMock()

            async def mock_empty_async_iter(self):
                return
                yield  # Never reached, but makes this a generator

            mock_async_event_store.__aiter__ = mock_empty_async_iter
            mock_async_wrapper.return_value = mock_async_event_store

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify running status
            assert data['status'] == ConversationStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_get_conversation_without_events(
        self, test_client, mock_conversation_metadata
    ):
        """Test conversation retrieval when EventStore is None or empty."""
        conversation_id = 'test-conversation-id'
        user_id = 'test-user-id'

        mock_conversation = MockConversation(conversation_id, user_id)

        with patch(
            'openhands.server.routes.integration.conversation.get_user_id'
        ) as mock_get_user_id, patch(
            'openhands.server.routes.integration.conversation.get_github_user_id'
        ) as mock_get_github_user_id, patch(
            'openhands.server.routes.integration.conversation.conversation_module'
        ) as mock_conversation_module, patch(
            'openhands.server.routes.integration.conversation.ConversationStoreImpl'
        ) as mock_conversation_store, patch(
            'openhands.server.routes.integration.conversation.conversation_manager'
        ) as mock_conversation_manager, patch(
            'openhands.server.routes.integration.conversation.EventStore'
        ) as mock_event_store_cls:
            # Setup basic mocks
            mock_get_user_id.return_value = user_id
            mock_get_github_user_id.return_value = None
            mock_conversation_module._get_conversation_by_id = AsyncMock(
                return_value=mock_conversation
            )

            # Mock conversation store
            mock_store_instance = MagicMock()
            mock_conversation_store.get_instance = AsyncMock(
                return_value=mock_store_instance
            )

            mock_metadata = MagicMock()
            mock_metadata.conversation_id = conversation_id
            mock_metadata.title = 'Test Conversation'
            mock_metadata.last_updated_at = mock_conversation_metadata[
                'last_updated_at'
            ]
            mock_metadata.created_at = mock_conversation_metadata['created_at']
            mock_metadata.selected_repository = 'test/repo'
            mock_store_instance.get_metadata = AsyncMock(return_value=mock_metadata)

            mock_conversation_manager.is_agent_loop_running = AsyncMock(
                return_value=False
            )
            mock_conversation_manager.file_store = MagicMock()

            # Mock EventStore to return None (simulating no event store)
            mock_event_store_cls.return_value = None

            response = test_client.get(
                f'/api/v1/integration/conversations/{conversation_id}',
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            data = response.json()

            # Should still return conversation info but without events
            assert data['conversation_id'] == conversation_id
            assert 'events' not in data or data['events'] is None

    @pytest.mark.asyncio
    async def test_create_conversation_with_space_data_success(self, test_client):
        """Test successful conversation creation with space_id and space_section_id."""
        conversation_id = 'test-conversation-id'
        space_id = 123
        space_section_id = 456

        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation, patch(
            'openhands.server.routes.integration.conversation.SpaceModule'
        ) as mock_space_module_cls:
            # Mock to return FastAPI JSONResponse with conversation_id
            from fastapi.responses import JSONResponse

            mock_new_conversation.return_value = JSONResponse(
                content={'status': 'ok', 'conversation_id': conversation_id}
            )

            # Mock SpaceModule
            mock_space_module = AsyncMock()
            mock_space_module.update_space_section_history = AsyncMock()
            mock_space_module_cls.return_value = mock_space_module

            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'research_mode': 'normal',
                'space_id': space_id,
                'space_section_id': space_section_id,
            }

            # Mock authentication middleware
            with patch(
                'openhands.server.middleware.JWTAuthMiddleware.dispatch'
            ) as mock_auth:

                async def mock_auth_dispatch(request, call_next):
                    # Simulate authenticated request with Authorization header
                    request.state.user_id = 'test-user-id'
                    request.state.user = type(
                        'User', (), {'mnemonic': 'test-mnemonic'}
                    )()
                    return await call_next(request)

                mock_auth.side_effect = mock_auth_dispatch

                response = test_client.post(
                    '/api/v1/integration/conversations/',
                    json=payload,
                    headers={'Authorization': 'Bearer test-token'},
                )

                assert response.status_code == 200
                response_data = response.json()
                assert response_data['conversation_id'] == conversation_id

                # Verify new_conversation was called
                mock_new_conversation.assert_called_once()

                # Verify SpaceModule was instantiated with correct authorization
                mock_space_module_cls.assert_called_once_with('Bearer test-token')

                # Verify update_space_section_history was called with correct parameters
                mock_space_module.update_space_section_history.assert_called_once_with(
                    space_id=str(space_id),
                    section_id=str(space_section_id),
                    conversation_id=conversation_id,
                )

    @pytest.mark.asyncio
    async def test_create_conversation_without_space_data(self, test_client):
        """Test conversation creation without space_id and space_section_id."""
        conversation_id = 'test-conversation-id'

        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation, patch(
            'openhands.server.routes.integration.conversation.SpaceModule'
        ) as mock_space_module_cls:
            # Mock to return FastAPI JSONResponse
            from fastapi.responses import JSONResponse

            mock_new_conversation.return_value = JSONResponse(
                content={'status': 'ok', 'conversation_id': conversation_id}
            )

            # Mock SpaceModule - should not be called
            mock_space_module = AsyncMock()
            mock_space_module_cls.return_value = mock_space_module

            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'research_mode': 'normal',
                # No space_id or space_section_id
            }

            response = test_client.post(
                '/api/v1/integration/conversations/',
                json=payload,
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data['conversation_id'] == conversation_id

            # Verify new_conversation was called
            mock_new_conversation.assert_called_once()

            # Verify SpaceModule was NOT instantiated since no space data provided
            mock_space_module_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_conversation_with_partial_space_data(self, test_client):
        """Test conversation creation with only space_id but no space_section_id."""
        conversation_id = 'test-conversation-id'

        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation, patch(
            'openhands.server.routes.integration.conversation.SpaceModule'
        ) as mock_space_module_cls:
            # Mock to return FastAPI JSONResponse
            from fastapi.responses import JSONResponse

            mock_new_conversation.return_value = JSONResponse(
                content={'status': 'ok', 'conversation_id': conversation_id}
            )

            # Mock SpaceModule - should not be called
            mock_space_module = AsyncMock()
            mock_space_module_cls.return_value = mock_space_module

            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'research_mode': 'normal',
                'space_id': 123,
                # Missing space_section_id
            }

            response = test_client.post(
                '/api/v1/integration/conversations/',
                json=payload,
                headers={'Authorization': 'Bearer test-token'},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data['conversation_id'] == conversation_id

            # Verify new_conversation was called
            mock_new_conversation.assert_called_once()

            # Verify SpaceModule was NOT called since space_section_id is missing
            mock_space_module_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_conversation_invalid_response_format(self, test_client):
        """Test conversation creation when new_conversation returns invalid JSON."""
        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation, patch(
            'openhands.server.routes.integration.conversation.SpaceModule'
        ) as mock_space_module_cls:
            # Mock to return response with invalid JSON

            mock_response = MagicMock()
            mock_response.body = b'invalid json'
            mock_new_conversation.return_value = mock_response

            # Mock SpaceModule - should not be called due to invalid response
            mock_space_module = AsyncMock()
            mock_space_module_cls.return_value = mock_space_module

            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'space_id': 123,
                'space_section_id': 456,
            }

            response = test_client.post(
                '/api/v1/integration/conversations/',
                json=payload,
                headers={'Authorization': 'Bearer test-token'},
            )

            # Should still return the response from new_conversation
            assert response.status_code == 200

            # Verify SpaceModule was NOT called due to conversation_id being None
            mock_space_module_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_conversation_space_update_error_handling(self, test_client):
        """Test that space update errors are handled gracefully by SpaceModule."""
        conversation_id = 'test-conversation-id'
        space_id = 123
        space_section_id = 456

        with patch(
            'openhands.server.routes.integration.conversation.new_conversation'
        ) as mock_new_conversation, patch(
            'openhands.server.routes.integration.conversation.SpaceModule'
        ) as mock_space_module_cls, patch(
            'openhands.server.modules.space.update_space_section_history'
        ) as mock_update_func, patch(
            'openhands.server.modules.space.logger'
        ) as mock_logger:
            # Mock to return FastAPI JSONResponse
            from fastapi.responses import JSONResponse

            mock_new_conversation.return_value = JSONResponse(
                content={'status': 'ok', 'conversation_id': conversation_id}
            )

            # Mock the underlying update function to raise an exception
            mock_update_func.side_effect = Exception('Space update failed')

            # Create a real SpaceModule instance so we test the actual error handling
            from openhands.server.modules.space import SpaceModule

            real_space_module = SpaceModule('Bearer test-token')
            mock_space_module_cls.return_value = real_space_module

            payload = {
                'initial_user_msg': 'Hello, I need help with coding',
                'space_id': space_id,
                'space_section_id': space_section_id,
            }

            response = test_client.post(
                '/api/v1/integration/conversations/',
                json=payload,
                headers={'Authorization': 'Bearer test-token'},
            )

            # Should still return success even if space update fails (error is handled internally)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data['conversation_id'] == conversation_id

            # Verify both functions were called
            mock_new_conversation.assert_called_once()
            mock_space_module_cls.assert_called_once_with('Bearer test-token')

            # Verify the underlying update function was called and error was logged
            mock_update_func.assert_called_once_with(
                space_id=str(space_id),
                section_id=str(space_section_id),
                conversation_id=conversation_id,
                bearer_token='Bearer test-token',
            )
            mock_logger.error.assert_called_once_with(
                'Error updating space section history: Space update failed'
            )
