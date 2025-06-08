import json
from contextlib import contextmanager
from datetime import datetime, timezone
from types import MappingProxyType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
    SuggestedTask,
    TaskType,
)
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.routes.manage_conversations import (
    ConversationResponse,
    InitSessionRequest,
    delete_conversation,
    get_conversation,
    new_conversation,
    search_conversations,
)
from openhands.server.routes.manage_conversations import app as conversation_app
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.server.user_auth.user_auth import AuthType
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
                'title': 'Some ServerConversation',
                'selected_repository': 'foobar',
                'conversation_id': 'some_conversation_id',
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


@pytest.fixture
def test_client():
    """Create a test client for the settings API."""
    app = FastAPI()
    app.include_router(conversation_app)
    return TestClient(app)


def create_new_test_conversation(
    test_request: InitSessionRequest, auth_type: AuthType | None = None
):
    # Create a mock UserSecrets object with the required custom_secrets attribute
    mock_user_secrets = MagicMock()
    mock_user_secrets.custom_secrets = MappingProxyType({})

    return new_conversation(
        data=test_request,
        user_id='test_user',
        provider_tokens=MappingProxyType({'github': 'token123'}),
        user_secrets=mock_user_secrets,
        auth_type=auth_type,
    )


@pytest.fixture
def provider_handler_mock():
    with patch(
        'openhands.server.routes.manage_conversations.ProviderHandler'
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.verify_repo_provider = AsyncMock(return_value=ProviderType.GITHUB)
        mock_cls.return_value = mock_instance
        yield mock_instance


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

                async def mock_get_connections(*args, **kwargs):
                    return {}

                async def get_agent_loop_info(*args, **kwargs):
                    return []

                mock_manager.get_running_agent_loops = mock_get_running_agent_loops
                mock_manager.get_connections = mock_get_connections
                mock_manager.get_agent_loop_info = get_agent_loop_info
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
                                    title='Some ServerConversation',
                                    created_at=datetime.fromisoformat(
                                        '2025-01-01T00:00:00+00:00'
                                    ),
                                    last_updated_at=datetime.fromisoformat(
                                        '2025-01-01T00:01:00+00:00'
                                    ),
                                    selected_repository='foobar',
                                    user_id='12345',
                                )
                            ]
                        )
                    )

                    result_set = await search_conversations(
                        page_id=None,
                        limit=20,
                        conversation_store=mock_store,
                    )

                    expected = ConversationInfoResultSet(
                        results=[
                            ConversationInfo(
                                conversation_id='some_conversation_id',
                                title='Some ServerConversation',
                                created_at=datetime.fromisoformat(
                                    '2025-01-01T00:00:00+00:00'
                                ),
                                last_updated_at=datetime.fromisoformat(
                                    '2025-01-01T00:01:00+00:00'
                                ),
                                status=ConversationStatus.STOPPED,
                                selected_repository='foobar',
                                num_connections=0,
                                url=None,
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
                title='Some ServerConversation',
                created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                selected_repository='foobar',
                user_id='12345',
            )
        )

        # Mock the conversation manager
        with patch(
            'openhands.server.routes.manage_conversations.conversation_manager'
        ) as mock_manager:
            mock_manager.is_agent_loop_running = AsyncMock(return_value=False)
            mock_manager.get_connections = AsyncMock(return_value={})
            mock_manager.get_agent_loop_info = AsyncMock(return_value=[])

            conversation = await get_conversation(
                'some_conversation_id', conversation_store=mock_store
            )

            expected = ConversationInfo(
                conversation_id='some_conversation_id',
                title='Some ServerConversation',
                created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                status=ConversationStatus.STOPPED,
                selected_repository='foobar',
                num_connections=0,
                url=None,
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
async def test_new_conversation_success(provider_handler_mock):
    """Test successful creation of a new conversation."""
    with _patch_store():
        # Mock the create_new_conversation function directly
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = MagicMock(
                conversation_id='test_conversation_id',
                url='https://my-conversation.com',
                session_api_key=None,
                status=ConversationStatus.RUNNING,
            )

            test_request = InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
                image_urls=['https://example.com/image.jpg'],
            )

            # Call new_conversation
            response = await create_new_test_conversation(test_request)

            # Verify the response
            assert isinstance(response, ConversationResponse)
            assert response.status == 'ok'
            # Don't check the exact conversation_id as it's now generated dynamically
            assert response.conversation_id is not None
            assert isinstance(response.conversation_id, str)

            # Verify that create_new_conversation was called with the correct arguments
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert call_args['user_id'] == 'test_user'
            assert call_args['selected_repository'] == 'test/repo'
            assert call_args['selected_branch'] == 'main'
            assert call_args['initial_user_msg'] == 'Hello, agent!'
            assert call_args['image_urls'] == ['https://example.com/image.jpg']
            assert call_args['conversation_trigger'] == ConversationTrigger.GUI


@pytest.mark.asyncio
async def test_new_conversation_with_suggested_task(provider_handler_mock):
    """Test creating a new conversation with a suggested task."""
    with _patch_store():
        # Mock the create_new_conversation function directly
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = MagicMock(
                conversation_id='test_conversation_id',
                url='https://my-conversation.com',
                session_api_key=None,
                status=ConversationStatus.RUNNING,
            )

            # Mock SuggestedTask.get_prompt_for_task
            with patch(
                'openhands.integrations.service_types.SuggestedTask.get_prompt_for_task'
            ) as mock_get_prompt:
                mock_get_prompt.return_value = (
                    'Please fix the failing checks in PR #123'
                )

                test_task = SuggestedTask(
                    git_provider=ProviderType.GITHUB,
                    task_type=TaskType.FAILING_CHECKS,
                    repo='test/repo',
                    issue_number=123,
                    title='Fix failing checks',
                )

                test_request = InitSessionRequest(
                    repository='test/repo',
                    selected_branch='main',
                    suggested_task=test_task,
                )

                # Call new_conversation
                response = await create_new_test_conversation(test_request)

                # Verify the response
                assert isinstance(response, ConversationResponse)
                assert response.status == 'ok'
                # Don't check the exact conversation_id as it's now generated dynamically
                assert response.conversation_id is not None
                assert isinstance(response.conversation_id, str)

                # Verify that create_new_conversation was called with the correct arguments
                mock_create_conversation.assert_called_once()
                call_args = mock_create_conversation.call_args[1]
                assert call_args['user_id'] == 'test_user'
                assert call_args['selected_repository'] == 'test/repo'
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
async def test_new_conversation_missing_settings(provider_handler_mock):
    """Test creating a new conversation when settings are missing."""
    with _patch_store():
        # Mock the create_new_conversation function to raise MissingSettingsError
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to raise MissingSettingsError
            mock_create_conversation.side_effect = MissingSettingsError(
                'Settings not found'
            )

            test_request = InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await create_new_test_conversation(test_request)

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400
            assert 'Settings not found' in response.body.decode('utf-8')
            assert 'CONFIGURATION$SETTINGS_NOT_FOUND' in response.body.decode('utf-8')


@pytest.mark.asyncio
async def test_new_conversation_invalid_session_api_key(provider_handler_mock):
    """Test creating a new conversation with an invalid API key."""
    with _patch_store():
        # Mock the create_new_conversation function to raise LLMAuthenticationError
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to raise LLMAuthenticationError
            mock_create_conversation.side_effect = LLMAuthenticationError(
                'Error authenticating with the LLM provider. Please check your API key'
            )

            test_request = InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await create_new_test_conversation(test_request)

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
                    title='Some ServerConversation',
                    created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
                    last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
                    selected_repository='foobar',
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
                mock_manager.get_connections = AsyncMock(return_value={})

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
async def test_new_conversation_with_bearer_auth(provider_handler_mock):
    """Test creating a new conversation with bearer authentication."""
    with _patch_store():
        # Mock the create_new_conversation function
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = MagicMock(
                conversation_id='test_conversation_id',
                url='https://my-conversation.com',
                session_api_key=None,
                status=ConversationStatus.RUNNING,
            )

            # Create the request object
            test_request = InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation with auth_type=BEARER
            response = await create_new_test_conversation(test_request, AuthType.BEARER)

            # Verify the response
            assert isinstance(response, ConversationResponse)
            assert response.status == 'ok'

            # Verify that create_new_conversation was called with REMOTE_API_KEY trigger
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert (
                call_args['conversation_trigger'] == ConversationTrigger.REMOTE_API_KEY
            )


@pytest.mark.asyncio
async def test_new_conversation_with_null_repository():
    """Test creating a new conversation with null repository."""
    with _patch_store():
        # Mock the create_new_conversation function
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = MagicMock(
                conversation_id='test_conversation_id',
                url='https://my-conversation.com',
                session_api_key=None,
                status=ConversationStatus.RUNNING,
            )

            # Create the request object with null repository
            test_request = InitSessionRequest(
                repository=None,  # Explicitly set to None
                selected_branch=None,
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await create_new_test_conversation(test_request)

            # Verify the response
            assert isinstance(response, ConversationResponse)
            assert response.status == 'ok'

            # Verify that create_new_conversation was called with None repository
            mock_create_conversation.assert_called_once()
            call_args = mock_create_conversation.call_args[1]
            assert call_args['selected_repository'] is None


@pytest.mark.asyncio
async def test_new_conversation_with_provider_authentication_error(
    provider_handler_mock,
):
    provider_handler_mock.verify_repo_provider = AsyncMock(
        side_effect=AuthenticationError('auth error')
    )

    """Test creating a new conversation when provider authentication fails."""
    with _patch_store():
        # Mock the create_new_conversation function
        with patch(
            'openhands.server.routes.manage_conversations.create_new_conversation'
        ) as mock_create_conversation:
            # Set up the mock to return a conversation ID
            mock_create_conversation.return_value = 'test_conversation_id'

            # Create the request object
            test_request = InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
            )

            # Call new_conversation
            response = await create_new_test_conversation(test_request)

            # Verify the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400
            assert json.loads(response.body.decode('utf-8')) == {
                'status': 'error',
                'message': 'auth error',
                'msg_id': 'STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR',
            }

            # Verify that verify_repo_provider was called with the repository
            provider_handler_mock.verify_repo_provider.assert_called_once_with(
                'test/repo', None
            )

            # Verify that create_new_conversation was not called
            mock_create_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_new_conversation_with_unsupported_params():
    """Test that unsupported parameters are rejected."""
    # Create a test request with an unsupported parameter
    with _patch_store():
        # Create a direct instance of InitSessionRequest to test validation
        with pytest.raises(Exception) as excinfo:
            # This should raise a validation error because of the extra parameter
            InitSessionRequest(
                repository='test/repo',
                selected_branch='main',
                initial_user_msg='Hello, agent!',
                unsupported_param='unsupported param',  # This should cause validation to fail
            )

        # Verify that the error message mentions the unsupported parameter
        assert 'Extra inputs are not permitted' in str(excinfo.value)
        assert 'unsupported_param' in str(excinfo.value)
