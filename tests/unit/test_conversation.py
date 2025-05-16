import json
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.routes.manage_conversations import (
    delete_conversation,
    get_conversation,
    search_conversations,
    update_conversation,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.locations import get_conversation_metadata_filename
from openhands.storage.memory import InMemoryFileStore


@contextmanager
def _patch_store():
    file_store = InMemoryFileStore()
    user_id = '12345'
    file_store.write(
        get_conversation_metadata_filename('some_conversation_id', user_id),
        json.dumps(
            {
                'title': 'Some Conversation',
                'selected_repository': 'foobar',
                'conversation_id': 'some_conversation_id',
                'github_user_id': '12345',
                'user_id': user_id,
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
                with patch(
                    'openhands.server.routes.manage_conversations.conversation_module'
                ) as mock_conversation_module:
                    with patch(
                        'openhands.server.routes.manage_conversations.get_user_id'
                    ) as mock_get_user_id:
                        with patch(
                            'openhands.server.routes.manage_conversations.get_github_user_id'
                        ) as mock_get_github_user_id:
                            # Mock user IDs
                            mock_get_user_id.return_value = '12345'
                            mock_get_github_user_id.return_value = None

                            # Mock the visibility check with an async function
                            async def mock_get_visibility(*args, **kwargs):
                                return {
                                    'items': [
                                        {'conversation_id': 'some_conversation_id'}
                                    ],
                                    'total': 1,
                                }

                            mock_conversation_module._get_conversation_visibility_by_user_id = mock_get_visibility

                            async def mock_get_running_agent_loops(*args, **kwargs):
                                return set()

                            mock_manager.get_running_agent_loops = (
                                mock_get_running_agent_loops
                            )
                            with patch(
                                'openhands.server.routes.manage_conversations.datetime'
                            ) as mock_datetime:
                                mock_datetime.now.return_value = datetime.fromisoformat(
                                    '2025-01-01T00:00:00+00:00'
                                )
                                mock_datetime.fromisoformat = datetime.fromisoformat
                                mock_datetime.timezone = timezone
                                result_set = await search_conversations(
                                    MagicMock(
                                        state=MagicMock(
                                            github_token='', user_id='12345'
                                        )
                                    ),
                                    page_id=None,
                                    limit=20,
                                    page=1,
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
                                    ],
                                    next_page_id=None,
                                    total=1,
                                )
                                assert result_set == expected


@pytest.mark.asyncio
async def test_get_conversation():
    with _patch_store():
        conversation = await get_conversation(
            'some_conversation_id',
            MagicMock(state=MagicMock(github_token='', user_id='12345')),
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
        assert (
            await get_conversation(
                'no_such_conversation',
                MagicMock(state=MagicMock(github_token='', user_id='12345')),
            )
            is None
        )


@pytest.mark.asyncio
async def test_update_conversation():
    with _patch_store():
        await update_conversation(
            MagicMock(state=MagicMock(github_token='', user_id='12345')),
            'some_conversation_id',
            'New Title',
        )
        conversation = await get_conversation(
            'some_conversation_id',
            MagicMock(state=MagicMock(github_token='', user_id='12345')),
        )
        expected = ConversationInfo(
            conversation_id='some_conversation_id',
            title='New Title',
            created_at=datetime.fromisoformat('2025-01-01T00:00:00+00:00'),
            last_updated_at=datetime.fromisoformat('2025-01-01T00:01:00+00:00'),
            status=ConversationStatus.STOPPED,
            selected_repository='foobar',
        )
        assert conversation == expected


@pytest.mark.asyncio
async def test_delete_conversation():
    with _patch_store():
        with patch.object(DockerRuntime, 'delete', return_value=None):
            # Mock the delete_thread function to prevent the headers.get() error
            with patch(
                'openhands.server.routes.manage_conversations.delete_thread',
                return_value=None,
            ):
                mock_request = MagicMock()
                # We don't need to worry about what headers.get returns now since the function is mocked

                await delete_conversation(
                    'some_conversation_id',
                    mock_request,
                )
                conversation = await get_conversation(
                    'some_conversation_id', MagicMock(state=MagicMock(github_token=''))
                )
                assert conversation is None
