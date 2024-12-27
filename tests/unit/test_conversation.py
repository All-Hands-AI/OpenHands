from datetime import datetime
import json
from unittest.mock import patch

import pytest
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_result_set import ConversationResultSet
from openhands.server.data_models.conversation_status import ConversationStatus
from openhands.server.routes.new_conversation import (
    get_conversation,
    search_conversations,
)
from openhands.storage.memory import InMemoryFileStore


@pytest.mark.asyncio
async def test_search_conversations():
    file_store = InMemoryFileStore()
    file_store.write(
        'sessions/some_conversation_id/metadata.json',
        json.dumps({'title': 'Some Conversation', 'selected_repository': 'foobar'}),
    )
    file_store.write(
        'sessions/some_conversation_id/events/0.json',
        json.dumps({'timestamp': '2025-01-01T00:00:00'}),
    )
    with patch(
        'openhands.server.routes.new_conversation.session_manager.file_store',
        file_store,
    ):
        result_set = await search_conversations()
        expected = ConversationResultSet(
            results=[
                ConversationInfo(
                    id='some_conversation_id',
                    title='Some Conversation',
                    last_updated_at=datetime.fromisoformat('2025-01-01T00:00:00'),
                    status=ConversationStatus.STOPPED,
                    selected_repository='foobar',
                )
            ]
        )
        assert result_set == expected


@pytest.mark.asyncio
async def test_get_conversation():
    file_store = InMemoryFileStore()
    file_store.write(
        'sessions/some_conversation_id/metadata.json',
        json.dumps({'title': 'Some Conversation', 'selected_repository': 'foobar'}),
    )
    file_store.write(
        'sessions/some_conversation_id/events/0.json',
        json.dumps({'timestamp': '2025-01-01T00:00:00'}),
    )
    with patch(
        'openhands.server.routes.new_conversation.session_manager.file_store',
        file_store,
    ):
        conversation = await get_conversation('some_conversation_id')
        expected = ConversationInfo(
            id='some_conversation_id',
            title='Some Conversation',
            last_updated_at=datetime.fromisoformat('2025-01-01T00:00:00'),
            status=ConversationStatus.STOPPED,
            selected_repository='foobar',
        )
        assert conversation == expected


@pytest.mark.asyncio
async def test_get_missing_conversation():
    with patch(
        'openhands.server.routes.new_conversation.session_manager.file_store',
        InMemoryFileStore({}),
    ):
        assert await get_conversation('no_such_conversation') is None
