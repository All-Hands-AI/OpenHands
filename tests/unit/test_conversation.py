import json
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse

from openhands.integrations.service_types import (
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
    InitSessionRequest,
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
