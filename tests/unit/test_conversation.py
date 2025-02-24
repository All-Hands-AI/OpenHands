import json
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.server.routes.manage_conversations import (
    delete_conversation,
    get_conversation,
    search_conversations,
    update_conversation,
)
from openhands.storage.data_models.conversation_info import ConversationInfo
from openhands.storage.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.memory import InMemoryFileStore


@contextmanager
def _patch_store():
    file_store = InMemoryFileStore()
    file_store.write(
        'sessions/some_conversation_id/metadata.json',
        json.dumps(
            {
                'title': 'Some Conversation',
                'selected_repository': 'foobar',
                'conversation_id': 'some_conversation_id',
                'github_user_id': '12345',
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
                    result_set = await search_conversations(
                        MagicMock(state=MagicMock(github_token=''))
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
        conversation = await get_conversation(
            'some_conversation_id', MagicMock(state=MagicMock(github_token=''))
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
                'no_such_conversation', MagicMock(state=MagicMock(github_token=''))
            )
            is None
        )


@pytest.mark.asyncio
async def test_update_conversation():
    with _patch_store():
        await update_conversation(
            MagicMock(state=MagicMock(github_token='')),
            'some_conversation_id',
            'New Title',
        )
        conversation = await get_conversation(
            'some_conversation_id', MagicMock(state=MagicMock(github_token=''))
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
            await delete_conversation(
                'some_conversation_id',
                MagicMock(state=MagicMock(github_token='')),
            )
            conversation = await get_conversation(
                'some_conversation_id', MagicMock(state=MagicMock(github_token=''))
            )
            assert conversation is None
