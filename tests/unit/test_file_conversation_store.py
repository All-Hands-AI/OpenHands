import json

import pytest

from openhands.storage.conversation.file_conversation_store import FileConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.memory import InMemoryFileStore

from openhands.storage.conversation.conversation_store import SortOrder


@pytest.mark.asyncio
async def test_load_store():
    store = FileConversationStore(InMemoryFileStore({}))
    expected = ConversationMetadata(
        conversation_id='some-conversation-id',
        github_user_id='some-user-id',
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
                'sessions/some-conversation-id/metadata.json': json.dumps(
                    {
                        'conversation_id': 'some-conversation-id',
                        'github_user_id': 12345,
                        'selected_repository': 'some-repo',
                        'title': "Let's talk about trains",
                        'created_at': '2025-01-16T19:51:04.886331Z',
                    }
                )
            }
        )
    )
    found = await store.get_metadata('some-conversation-id')
    assert found.github_user_id == '12345'


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
                'sessions/conv1/metadata.json': json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'github_user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'First conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                    }
                ),
                'sessions/conv2/metadata.json': json.dumps(
                    {
                        'conversation_id': 'conv2',
                        'github_user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Second conversation',
                        'created_at': '2025-01-17T19:51:04Z',
                    }
                ),
                'sessions/conv3/metadata.json': json.dumps(
                    {
                        'conversation_id': 'conv3',
                        'github_user_id': '123',
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
    # Should be sorted by date, newest first
    assert result.results[0].conversation_id == 'conv2'
    assert result.results[1].conversation_id == 'conv1'
    assert result.results[2].conversation_id == 'conv3'
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_pagination():
    # Create test data with 5 conversations
    store = FileConversationStore(
        InMemoryFileStore(
            {
                f'sessions/conv{i}/metadata.json': json.dumps(
                    {
                        'conversation_id': f'conv{i}',
                        'github_user_id': '123',
                        'selected_repository': 'repo1',
                        'title': f'Conversation {i}',
                        'created_at': f'2025-01-{15+i}T19:51:04Z',
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
                'sessions/conv1/metadata.json': json.dumps(
                    {
                        'conversation_id': 'conv1',
                        'github_user_id': '123',
                        'selected_repository': 'repo1',
                        'title': 'Valid conversation',
                        'created_at': '2025-01-16T19:51:04Z',
                    }
                ),
                'sessions/conv2/metadata.json': 'invalid json',  # Invalid conversation
            }
        )
    )

    result = await store.search()
    # Should return only the valid conversation
    assert len(result.results) == 1
    assert result.results[0].conversation_id == 'conv1'
    assert result.next_page_id is None


@pytest.mark.asyncio
async def test_search_sort_order_title():
    store = FileConversationStore(
        InMemoryFileStore({
            'sessions/conv1/metadata.json': json.dumps({
                'conversation_id': 'conv1',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'Banana',
                'created_at': '2025-01-16T19:51:04Z'
            }),
            'sessions/conv2/metadata.json': json.dumps({
                'conversation_id': 'conv2',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'Apple',
                'created_at': '2025-01-16T19:51:04Z'
            }),
            'sessions/conv3/metadata.json': json.dumps({
                'conversation_id': 'conv3',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'Cherry',
                'created_at': '2025-01-16T19:51:04Z'
            }),
        })
    )
    result = await store.search(sort_order=SortOrder.title)
    # Expected ascending order by title: Apple, Banana, Cherry
    assert [conv.conversation_id for conv in result.results] == ['conv2', 'conv1', 'conv3']
    result_desc = await store.search(sort_order=SortOrder.title_desc)
    # Expected descending order: Cherry, Banana, Apple
    assert [conv.conversation_id for conv in result_desc.results] == ['conv3', 'conv1', 'conv2']


@pytest.mark.asyncio
async def test_search_sort_order_last_updated():
    store = FileConversationStore(
        InMemoryFileStore({
            'sessions/conv1/metadata.json': json.dumps({
                'conversation_id': 'conv1',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'A',
                'created_at': '2025-01-16T19:51:04Z',
                'last_updated_at': '2025-01-16T19:51:04Z'
            }),
            'sessions/conv2/metadata.json': json.dumps({
                'conversation_id': 'conv2',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'B',
                'created_at': '2025-01-16T19:51:04Z',
                'last_updated_at': '2025-01-17T19:51:04Z'
            }),
            'sessions/conv3/metadata.json': json.dumps({
                'conversation_id': 'conv3',
                'github_user_id': 'user1',
                'selected_repository': 'repo1',
                'title': 'C',
                'created_at': '2025-01-16T19:51:04Z'
            }),
        })
    )
    result_asc = await store.search(sort_order=SortOrder.last_updated_at)
    ids = [conv.conversation_id for conv in result_asc.results]
    # In ascending order, conv2 (with last_updated_at 2025-01-17) should come last
    assert ids[-1] == 'conv2'
    result_desc = await store.search(sort_order=SortOrder.last_updated_at_desc)
    ids_desc = [conv.conversation_id for conv in result_desc.results]
    # In descending order, conv2 should come first
    assert ids_desc[0] == 'conv2'

