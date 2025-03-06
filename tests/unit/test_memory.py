import pytest

from openhands.events.action.agent import AgentRecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def file_store():
    """Create a temporary file store for testing."""
    return InMemoryFileStore()


@pytest.fixture
def event_stream(file_store):
    """Create a test event stream."""
    return EventStream(sid='test_sid', file_store=file_store)


@pytest.fixture
def memory(event_stream):
    """Create a test memory instance."""
    return Memory(event_stream, 'test_sid')


def test_is_on_first_user_message_true(memory, event_stream):
    """Test that _is_on_first_user_message returns True for the first user message.

    This test simulates the typical case where:
    1. First event is a MessageAction with id=0 and source=USER
    2. Second event is a RecallAction with id=1 and source=USER
    """
    # Add a MessageAction with source=USER
    message_action = MessageAction(content='test')
    message_action._source = EventSource.USER
    event_stream.add_event(message_action, EventSource.USER)

    # Add a RecallAction with source=USER
    recall_action = AgentRecallAction(query='test')
    recall_action._source = EventSource.USER
    event_stream.add_event(recall_action, EventSource.USER)

    assert memory._is_on_first_user_message(recall_action) is True


def test_is_on_first_user_message_false(memory, event_stream):
    """Test that _is_on_first_user_message returns False for subsequent user messages.

    This test simulates a case where:
    1. First event is a MessageAction with id=0 and source=USER
    2. Second event is a RecallAction with id=1 and source=USER
    3. Third event is a MessageAction with id=2 and source=USER
    4. Fourth event is a RecallAction with id=3 and source=USER
    """
    # Add first MessageAction with source=USER
    message_action1 = MessageAction(content='test1')
    message_action1._source = EventSource.USER
    event_stream.add_event(message_action1, EventSource.USER)

    # Add first RecallAction with source=USER
    recall_action1 = AgentRecallAction(query='test1')
    recall_action1._source = EventSource.USER
    event_stream.add_event(recall_action1, EventSource.USER)

    # Add second MessageAction with source=USER
    message_action2 = MessageAction(content='test2')
    message_action2._source = EventSource.USER
    event_stream.add_event(message_action2, EventSource.USER)

    # Add second RecallAction with source=USER
    recall_action2 = AgentRecallAction(query='test2')
    recall_action2._source = EventSource.USER
    event_stream.add_event(recall_action2, EventSource.USER)

    assert memory._is_on_first_user_message(recall_action2) is False
