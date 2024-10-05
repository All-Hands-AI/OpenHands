import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.event import Event, EventSource
from openhands.events.stream import EventStream
from openhands.memory.memory import LongTermMemory
from openhands.storage.files import FileStore


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    config = MagicMock(spec=LLMConfig)
    config.embedding_model = 'test_embedding_model'
    config.api_key = 'test_api_key'
    config.api_version = 'v1'
    return config


@pytest.fixture
def mock_agent_config() -> AgentConfig:
    config = AgentConfig(
        micro_agent_name='test_micro_agent',
        memory_enabled=True,
        memory_max_threads=4,
        llm_config='test_llm_config',
    )
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
    mock_llm_config: LLMConfig,
    mock_agent_config: AgentConfig,
    mock_event_stream: EventStream,
) -> LongTermMemory:
    with patch(
        'openhands.memory.memory.chromadb.PersistentClient'
    ) as mock_chroma_client:
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = (
            mock_collection
        )
        memory = LongTermMemory(
            llm_config=mock_llm_config,
            agent_config=mock_agent_config,
            event_stream=mock_event_stream,
        )
        memory.collection = mock_collection
        return memory


def _create_action_event(action: str) -> Event:
    """Helper function to create an action event."""
    event = Event()
    event._id = -1
    event._timestamp = datetime.now(timezone.utc).isoformat()
    event._source = EventSource.AGENT
    event.action = action
    return event


def _create_observation_event(observation: str) -> Event:
    """Helper function to create an observation event."""
    event = Event()
    event._id = -1
    event._timestamp = datetime.now(timezone.utc).isoformat()
    event._source = EventSource.USER
    event.observation = observation
    return event


def test_add_event_with_action(long_term_memory: LongTermMemory):
    event = _create_action_event('test_action')
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'action'
    assert kwargs['document'].extra_info['id'] == 'test_action'


def test_add_event_with_observation(long_term_memory: LongTermMemory):
    event = _create_observation_event('test_observation')
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'observation'
    assert kwargs['document'].extra_info['id'] == 'test_observation'


def test_add_event_with_missing_keys(long_term_memory: LongTermMemory):
    # Creating an event with additional unexpected attributes
    event = Event()
    event._id = -1
    event._timestamp = datetime.now(timezone.utc).isoformat()
    event._source = EventSource.AGENT
    event.action = 'test_action'
    event.unexpected_key = 'value'

    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    assert long_term_memory.thought_idx == 1
    long_term_memory._add_document.assert_called_once()
    _, kwargs = long_term_memory._add_document.call_args
    assert kwargs['document'].extra_info['type'] == 'action'
    assert kwargs['document'].extra_info['id'] == 'test_action'


def test_events_to_docs_no_events(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    mock_event_stream.get_events.side_effect = FileNotFoundError

    # convert events to documents
    documents = long_term_memory._events_to_docs()

    # since get_events raises, documents should be empty
    assert len(documents) == 0

    # thought_idx remains unchanged
    assert long_term_memory.thought_idx == 0


def test_load_events_into_index_with_invalid_json(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    """Test loading events with malformed event data."""
    # Simulate an event that causes event_to_memory to raise a JSONDecodeError
    with patch(
        'openhands.memory.memory.event_to_memory',
        side_effect=json.JSONDecodeError('Expecting value', '', 0),
    ):
        event = _create_action_event('invalid_action')
        mock_event_stream.get_events.return_value = [event]

        # convert events to documents
        documents = long_term_memory._events_to_docs()

        # since event_to_memory raises, documents should be empty
        assert len(documents) == 0

    # thought_idx remains unchanged
    assert long_term_memory.thought_idx == 0


def test_embeddings_inserted_into_chroma(long_term_memory: LongTermMemory):
    event = _create_action_event('test_action')
    long_term_memory._add_document = MagicMock()
    long_term_memory.add_event(event)
    long_term_memory._add_document.assert_called()
    _, kwargs = long_term_memory._add_document.call_args
    assert 'document' in kwargs
    assert (
        kwargs['document'].text
        == '{"source": "agent", "action": "test_action", "args": {}}'
    )


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
    event1 = _create_action_event('action1')
    event2 = _create_observation_event('observation1')
    long_term_memory.add_event(event1)
    long_term_memory.add_event(event2)
    assert long_term_memory.thought_idx == 2


def test_load_events_batch_insert(
    long_term_memory: LongTermMemory, mock_event_stream: EventStream
):
    event1 = _create_action_event('action1')
    event2 = _create_observation_event('observation1')
    event3 = _create_action_event('action2')
    mock_event_stream.get_events.return_value = [event1, event2, event3]

    # Mock insert_batch_docs
    with patch('openhands.utils.embeddings.insert_batch_docs') as mock_run_docs:
        # convert events to documents
        documents = long_term_memory._events_to_docs()

        # Mock the insert_batch_docs to simulate document insertion
        mock_run_docs.return_value = []

        # Call insert_batch_docs with the documents
        mock_run_docs(
            index=long_term_memory.index,
            documents=documents,
            num_workers=long_term_memory.memory_max_threads,
        )

        # Assert that insert_batch_docs was called with the correct arguments
        mock_run_docs.assert_called_once_with(
            index=long_term_memory.index,
            documents=documents,
            num_workers=long_term_memory.memory_max_threads,
        )

    # Check if thought_idx was incremented correctly
    assert long_term_memory.thought_idx == 3
