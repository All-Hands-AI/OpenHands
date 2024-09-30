from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.core.utils import json
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.memory.memory import LongTermMemory
from openhands.storage.files import FileStore


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    config = MagicMock(spec=LLMConfig)
    config.embedding_model = 'test_embedding_model'
    return config


@pytest.fixture
def mock_file_store() -> FileStore:
    store = MagicMock(spec=FileStore)
    store.sid = 'test_session'
    return store


@pytest.fixture
def mock_event_stream(mock_file_store: FileStore) -> EventStream:
    with patch('openhands.events.stream.EventStream') as MockEventStream:
        instance = MockEventStream.return_value
        instance.sid = 'test_session'
        instance.get_events = MagicMock()
        return instance


@pytest.fixture
def long_term_memory(
    mock_llm_config: LLMConfig, mock_event_stream: EventStream
) -> LongTermMemory:
    with patch('openhands.memory.memory.chromadb.Client') as mock_chroma_client:
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = (
            mock_collection
        )
        memory = LongTermMemory(
            llm_config=mock_llm_config, event_stream=mock_event_stream
        )
        memory.collection = mock_collection
        return memory


def test_add_event_with_action(long_term_memory: LongTermMemory):
    event = {'action': 'test_action'}
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'action'
    assert kwargs['document'].extra_info['id'] == 'test_action'


def test_add_event_with_observation(long_term_memory: LongTermMemory):
    event = {'observation': 'test_observation'}
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'observation'
    assert kwargs['document'].extra_info['id'] == 'test_observation'


def test_add_event_with_missing_keys(long_term_memory: LongTermMemory):
    event = {'action': 'test_action', 'unexpected_key': 'value'}
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'action'
    assert kwargs['document'].extra_info['id'] == 'test_action'


def test_load_events_into_index_success(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    mock_event_stream.get_events.return_value = [
        {'action': 'action1'},
        {'observation': 'observation1'},
    ]
    long_term_memory.index.insert_nodes = MagicMock()
    long_term_memory.load_events_into_index()
    assert long_term_memory.thought_idx == 2

    # Ensure insert_nodes was called with two nodes
    long_term_memory.index.insert_nodes.assert_called_once()
    args, _ = long_term_memory.index.insert_nodes.call_args
    assert len(args[0]) == 2
    assert args[0][0].extra_info['type'] == 'action'
    assert args[0][1].extra_info['type'] == 'observation'


def test_load_events_into_index_no_events(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    mock_event_stream.get_events.side_effect = FileNotFoundError
    long_term_memory.index.insert_nodes = MagicMock()
    long_term_memory.load_events_into_index()
    # Ensure insert_nodes was not called
    long_term_memory.index.insert_nodes.assert_not_called()


def test_load_events_into_index_with_invalid_json(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    """Test loading events with malformed event data."""
    # Simulate an event that causes event_to_memory to raise a JSONDecodeError
    # by configuring event_to_memory to raise when processing this event
    with patch(
        'openhands.memory.memory.event_to_memory',
        side_effect=json.JSONDecodeError('Expecting value', '', 0),
    ):
        mock_event_stream.get_events.return_value = [MagicMock(spec=Event)]
        long_term_memory.index.insert_nodes = MagicMock()

        with patch('logging.Logger.warning') as mock_warning:
            long_term_memory.load_events_into_index()
            mock_warning.assert_called()

        long_term_memory.index.insert_nodes.assert_not_called()


def test_embeddings_inserted_into_chroma(long_term_memory: LongTermMemory):
    event = {'action': 'test_action'}
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    long_term_memory._add_document.assert_called()
    _, kwargs = long_term_memory._add_document.call_args
    assert 'document' in kwargs
    assert kwargs['document'].text == '{"action": "test_action"}'


def test_search_returns_correct_results(long_term_memory: LongTermMemory):
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        MagicMock(get_text=MagicMock(return_value='result1')),
        MagicMock(get_text=MagicMock(return_value='result2')),
    ]
    with patch(
        'openhands.memory.memory.VectorIndexRetriever', return_value=mock_retriever
    ):
        results = long_term_memory.search(query='test query', k=2)
        assert results == ['result1', 'result2']
        mock_retriever.retrieve.assert_called_once_with('test query')


def test_search_with_no_results(long_term_memory: LongTermMemory):
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    with patch(
        'openhands.memory.memory.VectorIndexRetriever', return_value=mock_retriever
    ):
        results = long_term_memory.search(query='no results', k=5)
        assert results == []
        mock_retriever.retrieve.assert_called_once_with('no results')


def test_add_event_increment_thought_idx(long_term_memory: LongTermMemory):
    event1 = {'action': 'action1'}
    event2 = {'observation': 'observation1'}
    long_term_memory.add_event(event1)
    long_term_memory.add_event(event2)
    assert long_term_memory.thought_idx == 2


def test_load_events_batch_insert(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    mock_event_stream.get_events.return_value = [
        {'action': 'action1'},
        {'observation': 'observation1'},
        {'action': 'action2'},
    ]
    long_term_memory.index.insert_nodes = MagicMock()
    long_term_memory.load_events_into_index()
    assert long_term_memory.thought_idx == 3
    long_term_memory.index.insert_nodes.assert_called_once()
    args, _ = long_term_memory.index.insert_nodes.call_args
    assert len(args[0]) == 3
    assert args[0][0].extra_info['type'] == 'action'
    assert args[0][1].extra_info['type'] == 'observation'
    assert args[0][2].extra_info['type'] == 'action'
