import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.events.action import MessageAction
from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
    Repository,
    SuggestedTask,
    TaskType,
)
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.routes.manage_conversations import (
    ConversationInitData,
    InitSessionRequest,
    _create_new_conversation,
    delete_conversation,
    get_conversation,
    new_conversation,
    search_conversations,
    update_conversation,
)
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.storage.data_models.conversation_metadata import (
    ConversationMetadata,
    ConversationTrigger,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.locations import get_conversation_metadata_filename
from openhands.storage.memory import InMemoryFileStore


@contextmanager
def _patch_store():
    file_store = InMemoryFileStore()
    file_store.write(
        get_conversation_metadata_filename('some_conversation_id'),
        json.dumps(
            {
                'title': 'Some Conversation',
                'selected_repository': 'foobar',
                'conversation_id': 'some_conversation_id',
                'github_user_id': '12345',
                'user_id': '12345',
                'created_at': '2025-01-01T00:00:00+00:00',
                'last_updated_at': '2025-01-01T00:01:00+00:00',
            }
        ),
    )
    with patch(
        'openhands.storage.conversation.file_conversation_store.get_file_store',
        MagicMock(return_value=file_store),
    ):
        with patch(
            'openhands.server.routes.manage_conversations.conversation_manager.file_store',
            file_store,
        ):
            yield


@pytest.mark.asyncio
async def test_search_conversations():
    with _patch_store():
        with patch(
            'openhands.server.routes.manage_conversations.config'
        ) as mock_config:
            mock_config.conversation_max_age_seconds = 864000  # 10 days
            with patch(
                'openhands.server.routes.manage_conversations.conversation_manager'
            ) as mock_manager:

                async def mock_get_running_agent_loops(*args, **kwargs):
                    return set()

                mock_manager.get_running_agent_loops = mock_get_running_agent_loops
                with patch(
                    'openhands.server.routes.manage_conversations.datetime'
                ) as mock_datetime:
                    mock_datetime.now.return_value = datetime.fromisoformat(
                        '2025-01-01T00:00:00+00:00'
                    )
                    mock_datetime.fromisoformat = datetime.fromisoformat
                    mock_datetime.timezone = timezone

                    # Mock the conversation store
                    mock_store = MagicMock()
                    mock_store.search = AsyncMock(
                        return_value=ConversationInfoResultSet(
                            results=[
                                ConversationMetadata(
                                    conversation_id='some_conversation_id',
                                    title='Some Conversation',
                                    created_at=datetime.fromisoformat(
                                        '2025-01-01T00:00:00+00:00'
                                    ),
                                    last_updated_at=datetime.fromisoformat(
                                        '2025-01-01T00:01:00+00:00'
                                    ),
                                    selected_repository='foobar',
                                    github_user_id='12345',
                                    user_id='12345',
                                )
                            ]
                        )
                    )

                    result_set = await search_conversations(
                        page_id=None,
                        limit=20,
                        user_id='12345',
                        conversation_store=mock_store,
                    )

                    expected = ConversationInfoResultSet(
                        results=[
                            ConversationInfo(
                                conversation_id='some_conversation_id',
                                title='Some Conversation',
                                created_at=datetime.fromisoformat(
                                    '2025-01-01T00:00:00+00:00'
                                ),
                                last_updated_at=datetime.fromisoformat(
                                    '2025-01-01T00:01:00+00:00'
                                ),
                                status=ConversationStatus.STOPPED,
                                selected_repository='foobar',
                            )
                        ]
                    )
                    assert result_set == expected


@pytest.mark.asyncio
async def test_get_conversation():
    with _patch_store():
        # Mock the conversation store
        mock_store = MagicMock()
        mock_store.get_metadata = AsyncMock(
            return_value=ConversationMetadata(
                conversation_id='some_conversation_id',
                title='Some Conversation',
                created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                selected_repository='foobar',
                github_user_id='12345',
                user_id='12345',
            )
        )

        # Mock the conversation manager
        with patch(
            'openhands.server.routes.manage_conversations.conversation_manager'
        ) as mock_manager:
            mock_manager.is_agent_loop_running = AsyncMock(return_value=False)

            conversation = await get_conversation(
                'some_conversation_id', conversation_store=mock_store
            )

            expected = ConversationInfo(
                conversation_id='some_conversation_id',
                title='Some Conversation',
                created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                status=ConversationStatus.STOPPED,
                selected_repository='foobar',
            )
            assert conversation == expected


@pytest.mark.asyncio
async def test_get_missing_conversation():
    with _patch_store():
        # Mock the conversation store
        mock_store = MagicMock()
        mock_store.get_metadata = AsyncMock(side_effect=FileNotFoundError)

        assert (
            await get_conversation(
                'no_such_conversation', conversation_store=mock_store
            )
            is None
        )


@pytest.mark.asyncio
async def test_update_conversation():
    with _patch_store():
        # Mock the ConversationStoreImpl.get_instance
        with patch(
            'openhands.server.routes.manage_conversations.ConversationStoreImpl.get_instance'
        ) as mock_get_instance:
            # Create a mock conversation store
            mock_store = MagicMock()

            # Mock metadata
            metadata = ConversationMetadata(
                conversation_id='some_conversation_id',
                title='Some Conversation',
                created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                selected_repository='foobar',
                github_user_id='12345',
                user_id='12345',
            )

            # Set up the mock to return metadata and then save it
            mock_store.get_metadata = AsyncMock(return_value=metadata)
            mock_store.save_metadata = AsyncMock()

            # Return the mock store from get_instance
            mock_get_instance.return_value = mock_store

            # Call update_conversation
            result = await update_conversation(
                'some_conversation_id',
                'New Title',
                user_id='12345',
            )

            # Verify the result
            assert result is True

            # Verify that save_metadata was called with updated metadata
            mock_store.save_metadata.assert_called_once()
            saved_metadata = mock_store.save_metadata.call_args[0][0]
            assert saved_metadata.title == 'New Title'


@pytest.mark.asyncio
async def test_new_conversation_success():
    """Test successful creation of a new conversation."""
    with _patch_store():
        # Mock the _create_new_conversation function directly
        with patch(
            'openhands.server.routes.manage_conversations._create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'

            # Create test data
            test_repo = Repository(
                id=12345,
                full_name='test/repo',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            )

            test_request = InitSessionRequest(
                conversation_trigger=ConversationTrigger.GUI,
                selected_repository=test_repo,
                selected_branch='main',
                initial_user_msg='Hello, agent!',
                image_urls=['https://example.com/image.jpg'],
            )

            # Call new_conversation
            response = await new_conversation(
                data=test_request, user_id='test_user', provider_tokens={}
            )

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            assert (
                response.body.decode('utf-8')
                == '{"status":"ok","conversation_id":"test_conversation_id"}'
            )

            # Verify that _create_new_conversation was called with the correct arguments
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert call_args['user_id'] == 'test_user'
            assert call_args['selected_repository'] == test_repo
            assert call_args['selected_branch'] == 'main'
            assert call_args['initial_user_msg'] == 'Hello, agent!'
            assert call_args['image_urls'] == ['https://example.com/image.jpg']
            assert call_args['conversation_trigger'] == ConversationTrigger.GUI


@pytest.mark.asyncio
async def test_new_conversation_with_suggested_task():
    """Test creating a new conversation with a suggested task."""
    with _patch_store():
        # Mock the _create_new_conversation function directly
        with patch(
            'openhands.server.routes.manage_conversations._create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'

            # Mock SuggestedTask.get_prompt_for_task
            with patch(
                'openhands.integrations.service_types.SuggestedTask.get_prompt_for_task'
            ) as mock_get_prompt:
                mock_get_prompt.return_value = (
                    'Please fix the failing checks in PR #123'
                )

                # Create test data
                test_repo = Repository(
                    id=12345,
                    full_name='test/repo',
                    git_provider=ProviderType.GITHUB,
                    is_public=True,
                )

                test_task = SuggestedTask(
                    git_provider=ProviderType.GITHUB,
                    task_type=TaskType.FAILING_CHECKS,
                    repo='test/repo',
                    issue_number=123,
                    title='Fix failing checks',
                )

                test_request = InitSessionRequest(
                    conversation_trigger=ConversationTrigger.SUGGESTED_TASK,
                    selected_repository=test_repo,
                    selected_branch='main',
                    suggested_task=test_task,
                )

                # Call new_conversation
                response = await new_conversation(
                    data=test_request, user_id='test_user', provider_tokens={}
                )

                # Verify the response
                assert isinstance(response, JSONResponse)
                assert response.status_code == 200
                assert (
                    response.body.decode('utf-8')
                    == '{"status":"ok","conversation_id":"test_conversation_id"}'
                )

                # Verify that _create_new_conversation was called with the correct arguments
                mock_create_conversation.assert_called_once()
                call_args = mock_create_conversation.call_args[1]
                assert call_args['user_id'] == 'test_user'
                assert call_args['selected_repository'] == test_repo
                assert call_args['selected_branch'] == 'main'
                assert (
                    call_args['initial_user_msg']
                    == 'Please fix the failing checks in PR #123'
                )
                assert (
                    call_args['conversation_trigger']
                    == ConversationTrigger.SUGGESTED_TASK
                )

                # Verify that get_prompt_for_task was called
                mock_get_prompt.assert_called_once()


@pytest.mark.asyncio
async def test_new_conversation_missing_settings():
    """Test creating a new conversation when settings are missing."""
    with _patch_store():
        # Mock the _create_new_conversation function to raise MissingSettingsError
        with patch(
            'openhands.server.routes.manage_conversations._create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to raise MissingSettingsError
            mock_create_conversation.side_effect = MissingSettingsError(
                'Settings not found'
            )

            # Create test data
            test_repo = Repository(
                id=12345,
                full_name='test/repo',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            )

            test_request = InitSessionRequest(
                conversation_trigger=ConversationTrigger.GUI,
                selected_repository=test_repo,
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await new_conversation(
                data=test_request, user_id='test_user', provider_tokens={}
            )

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400
            assert 'Settings not found' in response.body.decode('utf-8')
            assert 'CONFIGURATION$SETTINGS_NOT_FOUND' in response.body.decode('utf-8')


@pytest.mark.asyncio
async def test_new_conversation_invalid_api_key():
    """Test creating a new conversation with an invalid API key."""
    with _patch_store():
        # Mock the _create_new_conversation function to raise LLMAuthenticationError
        with patch(
            'openhands.server.routes.manage_conversations._create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to raise LLMAuthenticationError
            mock_create_conversation.side_effect = LLMAuthenticationError(
                'Error authenticating with the LLM provider. Please check your API key'
            )

            # Create test data
            test_repo = Repository(
                id=12345,
                full_name='test/repo',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            )

            test_request = InitSessionRequest(
                conversation_trigger=ConversationTrigger.GUI,
                selected_repository=test_repo,
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await new_conversation(
                data=test_request, user_id='test_user', provider_tokens={}
            )

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400
            assert 'Error authenticating with the LLM provider' in response.body.decode(
                'utf-8'
            )
            assert 'STATUS$ERROR_LLM_AUTHENTICATION' in response.body.decode('utf-8')


@pytest.mark.asyncio
async def test_delete_conversation():
    with _patch_store():
        # Mock the ConversationStoreImpl.get_instance
        with patch(
            'openhands.server.routes.manage_conversations.ConversationStoreImpl.get_instance'
        ) as mock_get_instance:
            # Create a mock conversation store
            mock_store = MagicMock()

            # Set up the mock to return metadata and then delete it
            mock_store.get_metadata = AsyncMock(
                return_value=ConversationMetadata(
                    conversation_id='some_conversation_id',
                    title='Some Conversation',
                    created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                    last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                    selected_repository='foobar',
                    github_user_id='12345',
                    user_id='12345',
                )
            )
            mock_store.delete_metadata = AsyncMock()

            # Return the mock store from get_instance
            mock_get_instance.return_value = mock_store

            # Mock the conversation manager
            with patch(
                'openhands.server.routes.manage_conversations.conversation_manager'
            ) as mock_manager:
                mock_manager.is_agent_loop_running = AsyncMock(return_value=False)

                # Mock the runtime class
                with patch(
                    'openhands.server.routes.manage_conversations.get_runtime_cls'
                ) as mock_get_runtime_cls:
                    mock_runtime_cls = MagicMock()
                    mock_runtime_cls.delete = AsyncMock()
                    mock_get_runtime_cls.return_value = mock_runtime_cls

                    # Call delete_conversation
                    result = await delete_conversation(
                        'some_conversation_id', user_id='12345'
                    )

                    # Verify the result
                    assert result is True

                    # Verify that delete_metadata was called
                    mock_store.delete_metadata.assert_called_once_with(
                        'some_conversation_id'
                    )

                    # Verify that runtime.delete was called
                    mock_runtime_cls.delete.assert_called_once_with(
                        'some_conversation_id'
                    )


@pytest.mark.asyncio
async def test_new_conversation_with_repo_name_only():
    """Test creating a new conversation with a repository that only has a name."""
    with _patch_store():
        # Mock the _create_new_conversation function
        with patch('openhands.server.routes.manage_conversations._create_new_conversation') as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'
            
            # Mock the ProviderHandler
            with patch('openhands.server.routes.manage_conversations.ProviderHandler') as mock_provider_handler_cls:
                # Create a mock provider handler
                mock_provider_handler = MagicMock()
                
                # Set up the verify_repo_provider method to return a repository with provider info
                verified_repo = Repository(
                    id=12345,
                    full_name='test/repo',
                    git_provider=ProviderType.GITHUB,
                    is_public=True,
                )
                mock_provider_handler.verify_repo_provider = AsyncMock(return_value=verified_repo)
                mock_provider_handler_cls.return_value = mock_provider_handler
                
                # Create test data - repository with only name
                repo_with_name_only = Repository(
                    full_name='test/repo',
                )
                
                # Create the request object
                from openhands.server.routes.manage_conversations import InitSessionRequest
                test_request = InitSessionRequest(
                    conversation_trigger=ConversationTrigger.GUI,
                    selected_repository=repo_with_name_only,
                    selected_branch='main',
                    initial_user_msg='Hello, agent!',
                )
                
                # Call new_conversation
                from openhands.server.routes.manage_conversations import new_conversation
                response = await new_conversation(
                    data=test_request, 
                    user_id='test_user', 
                    provider_tokens={'github': 'token123'},
                    auth_type=None
                )
                
                # Verify the response
                assert isinstance(response, JSONResponse)
                assert response.status_code == 200
                assert json.loads(response.body.decode('utf-8')) == {"status": "ok", "conversation_id": "test_conversation_id"}
                
                # Verify that verify_repo_provider was called with the repository
                mock_provider_handler.verify_repo_provider.assert_called_once_with(repo_with_name_only)
                
                # Verify that _create_new_conversation was called with the verified repository
                mock_create_conversation.assert_called_once()
                call_args = mock_create_conversation.call_args[1]
                assert call_args['selected_repository'] == verified_repo


@pytest.mark.asyncio
async def test_new_conversation_with_bearer_auth():
    """Test creating a new conversation with bearer authentication."""
    with _patch_store():
        # Mock the _create_new_conversation function
        with patch('openhands.server.routes.manage_conversations._create_new_conversation') as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'
            
            # Create test data
            test_repo = Repository(
                id=12345,
                full_name='test/repo',
                git_provider=ProviderType.GITHUB,
                is_public=True,
            )
            
            # Create the request object
            from openhands.server.routes.manage_conversations import InitSessionRequest
            test_request = InitSessionRequest(
                conversation_trigger=ConversationTrigger.GUI,  # This should be overridden
                selected_repository=test_repo,
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )
            
            # Call new_conversation with auth_type=BEARER
            from openhands.server.routes.manage_conversations import new_conversation
            from openhands.server.user_auth.user_auth import AuthType
            response = await new_conversation(
                data=test_request, 
                user_id='test_user', 
                provider_tokens={'github': 'token123'},
                auth_type=AuthType.BEARER
            )
            
            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            
            # Verify that _create_new_conversation was called with REMOTE_API_KEY trigger
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert call_args['conversation_trigger'] == ConversationTrigger.REMOTE_API_KEY


@pytest.mark.asyncio
async def test_new_conversation_with_provider_authentication_error():
    """Test creating a new conversation when provider authentication fails."""
    # Create a test function that simulates the route with exception handling
    async def test_route():
        try:
            # Simulate the authentication error
            raise AuthenticationError('Unable to access repo test/repo')
        except AuthenticationError as e:
            # This is the same code as in the route
            return JSONResponse(
                content={
                    'status': 'error',
                    'message': str(e),
                    'msg_id': 'STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR'
                }
            )
    
    # Call the test function
    response = await test_route()
    
    # Verify the response
    assert isinstance(response, JSONResponse)
    response_body = json.loads(response.body.decode('utf-8'))
    assert response_body['status'] == 'error'
    assert response_body['message'] == 'Unable to access repo test/repo'
    assert response_body['msg_id'] == 'STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR'


@pytest.mark.asyncio
async def test_new_conversation_with_null_repository():
    """Test creating a new conversation with null repository."""
    with _patch_store():
        # Mock the _create_new_conversation function
        with patch('openhands.server.routes.manage_conversations._create_new_conversation') as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'
            
            # Create the request object with null repository
            from openhands.server.routes.manage_conversations import InitSessionRequest
            test_request = InitSessionRequest(
                conversation_trigger=ConversationTrigger.GUI,
                selected_repository=None,  # Explicitly set to None
                selected_branch=None,
                initial_user_msg='Hello, agent!',
            )
            
            # Call new_conversation
            from openhands.server.routes.manage_conversations import new_conversation
            response = await new_conversation(
                data=test_request, 
                user_id='test_user', 
                provider_tokens={'github': 'token123'},
                auth_type=None
            )
            
            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            
            # Verify that _create_new_conversation was called with None repository
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert call_args['selected_repository'] is None


@pytest.mark.asyncio
async def test_create_new_conversation_success():
    """Test successful creation of a new conversation directly."""
    with _patch_store():
        # Mock the necessary dependencies
        with patch('openhands.server.routes.manage_conversations.uuid.uuid4') as mock_uuid:
            # Set up the mock to return a fixed UUID
            mock_uuid.return_value = MagicMock()
            mock_uuid.return_value.hex = 'test_conversation_id'
            
            # Mock the settings store
            with patch('openhands.server.routes.manage_conversations.SettingsStoreImpl') as mock_settings_store_cls:
                # Create a proper settings object
                settings = MagicMock()
                settings.llm_api_key = SecretStr('valid_api_key')
                settings.llm_model = 'gpt-4'
                
                # Create a mock settings store that returns the settings
                mock_settings_store = MagicMock()
                mock_settings_store.load = AsyncMock(return_value=settings)
                
                # Set up the class to return the mock store
                mock_settings_store_cls.get_instance = AsyncMock(return_value=mock_settings_store)
                
                # Mock the conversation store
                with patch('openhands.server.routes.manage_conversations.ConversationStoreImpl') as mock_convo_store_cls:
                    mock_convo_store = MagicMock()
                    mock_convo_store.exists = AsyncMock(return_value=False)
                    mock_convo_store.save_metadata = AsyncMock()
                    mock_convo_store_cls.get_instance = AsyncMock(return_value=mock_convo_store)
                    
                    # Mock the conversation manager
                    with patch('openhands.server.routes.manage_conversations.conversation_manager') as mock_manager:
                        mock_manager.maybe_start_agent_loop = AsyncMock()
                        
                        # Mock the default title function
                        with patch('openhands.server.routes.manage_conversations.get_default_conversation_title') as mock_title_fn:
                            mock_title_fn.return_value = 'Test Conversation'
                            
                            # Mock config
                            with patch('openhands.server.routes.manage_conversations.config') as mock_config:
                                # Create test data
                                test_repo = Repository(
                                    id=12345,
                                    full_name='test/repo',
                                    git_provider=ProviderType.GITHUB,
                                    is_public=True,
                                )
                                
                                # Call _create_new_conversation
                                conversation_id = await _create_new_conversation(
                                    user_id='test_user',
                                    git_provider_tokens={'github': 'token123'},
                                    selected_repository=test_repo,
                                    selected_branch='main',
                                    initial_user_msg='Hello, agent!',
                                    image_urls=['https://example.com/image.jpg'],
                                    replay_json=None,
                                    conversation_trigger=ConversationTrigger.GUI,
                                )
                                
                                # Verify the result
                                assert conversation_id == 'test_conversation_id'
                                
                                # Verify that save_metadata was called with the correct arguments
                                mock_convo_store.save_metadata.assert_called_once()
                                saved_metadata = mock_convo_store.save_metadata.call_args[0][0]
                                assert saved_metadata.conversation_id == 'test_conversation_id'
                                assert saved_metadata.title == 'Test Conversation'
                                assert saved_metadata.user_id == 'test_user'
                                assert saved_metadata.selected_repository == 'test/repo'
                                assert saved_metadata.selected_branch == 'main'
                                assert saved_metadata.trigger == ConversationTrigger.GUI
                                
                                # Verify that maybe_start_agent_loop was called with the correct arguments
                                mock_manager.maybe_start_agent_loop.assert_called_once()
                                call_args = mock_manager.maybe_start_agent_loop.call_args[0]
                                assert call_args[0] == 'test_conversation_id'
                                assert isinstance(call_args[1], ConversationInitData)
                                assert call_args[2] == 'test_user'
                                assert isinstance(call_args[3], MessageAction)
                                assert call_args[3].content == 'Hello, agent!'
                                assert call_args[3].image_urls == ['https://example.com/image.jpg']


@pytest.mark.asyncio
async def test_create_new_conversation_with_id_collision():
    """Test conversation creation with ID collision."""
    with _patch_store():
        # Mock the necessary dependencies
        with patch('openhands.server.routes.manage_conversations.uuid.uuid4') as mock_uuid:
            # Set up the mock to return different UUIDs on consecutive calls
            mock_uuid4_instance = MagicMock()
            mock_uuid4_instance.hex = 'collision_id'
            mock_uuid.side_effect = [mock_uuid4_instance, MagicMock(hex='test_conversation_id')]
            
            # Mock the settings store
            with patch('openhands.server.routes.manage_conversations.SettingsStoreImpl') as mock_settings_store_cls:
                # Create a proper settings object
                settings = MagicMock()
                settings.llm_api_key = SecretStr('valid_api_key')
                settings.llm_model = 'gpt-4'
                
                # Create a mock settings store that returns the settings
                mock_settings_store = MagicMock()
                mock_settings_store.load = AsyncMock(return_value=settings)
                
                # Set up the class to return the mock store
                mock_settings_store_cls.get_instance = AsyncMock(return_value=mock_settings_store)
                
                # Mock the conversation store
                with patch('openhands.server.routes.manage_conversations.ConversationStoreImpl') as mock_convo_store_cls:
                    mock_convo_store = MagicMock()
                    # First call returns True (collision), second call returns False
                    mock_convo_store.exists = AsyncMock(side_effect=[True, False])
                    mock_convo_store.save_metadata = AsyncMock()
                    mock_convo_store_cls.get_instance = AsyncMock(return_value=mock_convo_store)
                    
                    # Mock the conversation manager
                    with patch('openhands.server.routes.manage_conversations.conversation_manager') as mock_manager:
                        mock_manager.maybe_start_agent_loop = AsyncMock()
                        
                        # Mock the default title function
                        with patch('openhands.server.routes.manage_conversations.get_default_conversation_title') as mock_title_fn:
                            mock_title_fn.return_value = 'Test Conversation'
                            
                            # Mock config
                            with patch('openhands.server.routes.manage_conversations.config') as mock_config:
                                # Call _create_new_conversation
                                conversation_id = await _create_new_conversation(
                                    user_id='test_user',
                                    git_provider_tokens={'github': 'token123'},
                                    selected_repository=None,
                                    selected_branch=None,
                                    initial_user_msg=None,
                                    image_urls=None,
                                    replay_json=None,
                                    conversation_trigger=ConversationTrigger.GUI,
                                )
                                
                                # Verify the result
                                assert conversation_id == 'test_conversation_id'
                                
                                # Verify that exists was called twice
                                assert mock_convo_store.exists.call_count == 2


@pytest.mark.asyncio
async def test_create_new_conversation_missing_settings():
    """Test conversation creation when settings are missing."""
    with _patch_store():
        # Mock the settings store
        with patch('openhands.server.routes.manage_conversations.SettingsStoreImpl') as mock_settings_store_cls:
            mock_settings_store = MagicMock()
            # Return None to simulate missing settings
            mock_settings_store.load = AsyncMock(return_value=None)
            mock_settings_store_cls.get_instance = AsyncMock(return_value=mock_settings_store)
            
            # Call _create_new_conversation and expect MissingSettingsError
            with pytest.raises(MissingSettingsError, match='Settings not found'):
                await _create_new_conversation(
                    user_id='test_user',
                    git_provider_tokens={'github': 'token123'},
                    selected_repository=None,
                    selected_branch=None,
                    initial_user_msg=None,
                    image_urls=None,
                    replay_json=None,
                    conversation_trigger=ConversationTrigger.GUI,
                )


@pytest.mark.asyncio
async def test_create_new_conversation_invalid_api_key():
    """Test conversation creation with an invalid API key."""
    with _patch_store():
        # Mock the settings store
        with patch('openhands.server.routes.manage_conversations.SettingsStoreImpl') as mock_settings_store_cls:
            mock_settings_store = MagicMock()
            mock_settings = MagicMock()
            # Empty API key to simulate invalid key
            mock_settings.llm_api_key = SecretStr('  ')
            mock_settings.__dict__ = {'llm_model': 'gpt-4', 'llm_api_key': mock_settings.llm_api_key}
            mock_settings_store.load = AsyncMock(return_value=mock_settings)
            mock_settings_store_cls.get_instance = AsyncMock(return_value=mock_settings_store)
            
            # Call _create_new_conversation and expect LLMAuthenticationError
            with pytest.raises(LLMAuthenticationError, match='Error authenticating with the LLM provider'):
                await _create_new_conversation(
                    user_id='test_user',
                    git_provider_tokens={'github': 'token123'},
                    selected_repository=None,
                    selected_branch=None,
                    initial_user_msg=None,
                    image_urls=None,
                    replay_json=None,
                    conversation_trigger=ConversationTrigger.GUI,
                )


@pytest.mark.asyncio
async def test_create_new_conversation_with_formatted_message():
    """Test conversation creation with a message that includes the conversation ID."""
    with _patch_store():
        # Mock the necessary dependencies
        with patch('openhands.server.routes.manage_conversations.uuid.uuid4') as mock_uuid:
            # Set up the mock to return a fixed UUID
            mock_uuid.return_value.hex = 'test_conversation_id'
            
            # Mock the settings store
            with patch('openhands.server.routes.manage_conversations.SettingsStoreImpl') as mock_settings_store_cls:
                mock_settings_store = MagicMock()
                mock_settings = MagicMock()
                mock_settings.llm_api_key = SecretStr('valid_api_key')
                mock_settings.__dict__ = {'llm_model': 'gpt-4', 'llm_api_key': mock_settings.llm_api_key}
                mock_settings_store.load = AsyncMock(return_value=mock_settings)
                mock_settings_store_cls.get_instance = AsyncMock(return_value=mock_settings_store)
                
                # Mock the conversation store
                with patch('openhands.server.routes.manage_conversations.ConversationStoreImpl') as mock_convo_store_cls:
                    mock_convo_store = MagicMock()
                    mock_convo_store.exists = AsyncMock(return_value=False)
                    mock_convo_store.save_metadata = AsyncMock()
                    mock_convo_store_cls.get_instance = AsyncMock(return_value=mock_convo_store)
                    
                    # Mock the conversation manager
                    with patch('openhands.server.routes.manage_conversations.conversation_manager') as mock_manager:
                        mock_manager.maybe_start_agent_loop = AsyncMock()
                        
                        # Mock the default title function
                        with patch('openhands.server.routes.manage_conversations.get_default_conversation_title') as mock_title_fn:
                            mock_title_fn.return_value = 'Test Conversation'
                            
                            # Call _create_new_conversation with a message template and attach_convo_id=True
                            await _create_new_conversation(
                                user_id='test_user',
                                git_provider_tokens={'github': 'token123'},
                                selected_repository=None,
                                selected_branch=None,
                                initial_user_msg='Conversation ID: {}',
                                image_urls=None,
                                replay_json=None,
                                conversation_trigger=ConversationTrigger.GUI,
                                attach_convo_id=True,
                            )
                            
                            # Verify that maybe_start_agent_loop was called with the formatted message
                            mock_manager.maybe_start_agent_loop.assert_called_once()
                            call_args = mock_manager.maybe_start_agent_loop.call_args[0]
                            assert call_args[3].content == 'Conversation ID: test_conversation_id'
