import json
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
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
