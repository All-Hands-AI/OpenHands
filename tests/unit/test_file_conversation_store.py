import json

import pytest

from openhands.storage.conversation.file_conversation_store import FileConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.locations import get_conversation_metadata_filename
from openhands.storage.memory import InMemoryFileStore


@pytest.mark.asyncio
async def test_load_store():
    store = FileConversationStore(InMemoryFileStore({}))
    expected = ConversationMetadata(
        conversation_id='some-conversation-id',
        user_id='some-user-id',
        selected_repository='some-repo',
        title="Let's talk about trains",
    )
    await store.save_metadata(expected)
    found = await store.get_metadata('some-conversation-id')
    assert expected == found


@pytest.mark.asyncio
async def test_load_int_user_id():
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('some-conversation-id'): json.dumps(
                    {
                        'conversation_id': 'some-conversation-id',
                        'user_id': '67890',
                        'selected_repository': 'some-repo',
                        'title': "Let's talk about trains",
                        'created_at': '2025-01-16T19:51:04.886331Z',
                    }
                )
            }
        )
    )
    found = await store.get_metadata('some-conversation-id')
    assert found.user_id == '67890'


@pytest.mark.asyncio
async def test_search_empty():
    store = FileConversationStore(InMemoryFileStore({}))
    result = await store.search()
    assert len(result.results) == 0
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_basic():
    # Create test data with 3 conversations at different dates
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('conv1'): json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'First conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                    }
                ),
                get_conversation_metadata_filename('conv2'): json.dumps(
                    {
                        'conversation_id': 'conv2',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Second conversation',
                        'created_at': '2025-01-17T19:51:04Z',
                    }
                ),
                get_conversation_metadata_filename('conv3'): json.dumps(
                    {
                        'conversation_id': 'conv3',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Third conversation',
                        'created_at': '2025-01-15T19:51:04Z',
                    }
                ),
            }
        )
    )

    result = await store.search()
    assert len(result.results) == 3
    # Should be sorted by created_at date (since no last_updated_at), newest first
    assert result.results[0].conversation_id == 'conv2'
    assert result.results[1].conversation_id == 'conv1'
    assert result.results[2].conversation_id == 'conv3'
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_sort_by_last_updated_at():
    # Create test data with conversations that have both created_at and last_updated_at
    # The last_updated_at should take precedence for sorting
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('conv1'): json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'First conversation',
                        'created_at': '2025-01-17T19:51:04Z',  # Created second
                        'last_updated_at': '2025-01-15T20:00:00Z',  # Updated first (oldest)
                    }
                ),
                get_conversation_metadata_filename('conv2'): json.dumps(
                    {
                        'conversation_id': 'conv2',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Second conversation',
                        'created_at': '2025-01-15T19:51:04Z',  # Created first (oldest)
                        'last_updated_at': '2025-01-18T20:00:00Z',  # Updated most recently
                    }
                ),
                get_conversation_metadata_filename('conv3'): json.dumps(
                    {
                        'conversation_id': 'conv3',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Third conversation',
                        'created_at': '2025-01-16T19:51:04Z',  # Created third
                        'last_updated_at': '2025-01-17T20:00:00Z',  # Updated second
                    }
                ),
            }
        )
    )

    result = await store.search()
    assert len(result.results) == 3
    # Should be sorted by last_updated_at, newest first
    assert result.results[0].conversation_id == 'conv2'  # Most recently updated
    assert result.results[1].conversation_id == 'conv3'  # Second most recently updated
    assert result.results[2].conversation_id == 'conv1'  # Least recently updated
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_mixed_last_updated_at():
    # Test conversations with mixed presence of last_updated_at
    # Some have last_updated_at, some don't (should fall back to created_at)
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('conv1'): json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'First conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                        'last_updated_at': '2025-01-18T20:00:00Z',  # Most recent update
                    }
                ),
                get_conversation_metadata_filename('conv2'): json.dumps(
                    {
                        'conversation_id': 'conv2',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Second conversation',
                        'created_at': '2025-01-17T19:51:04Z',  # No last_updated_at, falls back to created_at
                    }
                ),
                get_conversation_metadata_filename('conv3'): json.dumps(
                    {
                        'conversation_id': 'conv3',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Third conversation',
                        'created_at': '2025-01-15T19:51:04Z',
                        'last_updated_at': '2025-01-16T20:00:00Z',  # Older update
                    }
                ),
            }
        )
    )

    result = await store.search()
    assert len(result.results) == 3
    # Should be sorted by last_updated_at (or created_at as fallback), newest first
    assert result.results[0].conversation_id == 'conv1'  # Most recent last_updated_at
    assert (
        result.results[1].conversation_id == 'conv2'
    )  # Falls back to created_at (2025-01-17)
    assert (
        result.results[2].conversation_id == 'conv3'
    )  # Older last_updated_at (2025-01-16)
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_pagination():
    # Create test data with 5 conversations
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename(f'conv{i}'): json.dumps(
                    {
                        'conversation_id': f'conv{i}',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': f'ServerConversation {i}',
                        'created_at': f'2025-01-{15 + i}T19:51:04Z',
                    }
                )
                for i in range(1, 6)
            }
        )
    )

    # Test with limit of 2
    result = await store.search(limit=2)
    assert len(result.results) == 2
    assert result.results[0].conversation_id == 'conv5'  # newest first
    assert result.results[1].conversation_id == 'conv4'
    assert result.next_page_id is not None

    # Get next page using the next_page_id
    result2 = await store.search(page_id=result.next_page_id, limit=2)
    assert len(result2.results) == 2
    assert result2.results[0].conversation_id == 'conv3'
    assert result2.results[1].conversation_id == 'conv2'
    assert result2.next_page_id is not None

    # Get last page
    result3 = await store.search(page_id=result2.next_page_id, limit=2)
    assert len(result3.results) == 1
    assert result3.results[0].conversation_id == 'conv1'
    assert result3.next_page_id is None


@pytest.mark.asyncio
async def test_search_with_invalid_conversation():
    # Test handling of invalid conversation data
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('conv1'): json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Valid conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                    }
                ),
                get_conversation_metadata_filename(
                    'conv2'
                ): 'invalid json',  # Invalid conversation
            }
        )
    )

    result = await store.search()
    # Should return only the valid conversation
    assert len(result.results) == 1
    assert result.results[0].conversation_id == 'conv1'
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_get_all_metadata():
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename('conv1'): json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'First conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                    }
                ),
                get_conversation_metadata_filename('conv2'): json.dumps(
                    {
                        'conversation_id': 'conv2',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Second conversation',
                        'created_at': '2025-01-17T19:51:04Z',
                    }
                ),
            }
        )
    )

    results = await store.get_all_metadata(['conv1', 'conv2'])
    assert len(results) == 2
    assert results[0].conversation_id == 'conv1'
    assert results[0].title == 'First conversation'
    assert results[1].conversation_id == 'conv2'
    assert results[1].title == 'Second conversation'
