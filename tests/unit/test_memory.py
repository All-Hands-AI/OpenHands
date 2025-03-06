from unittest.mock import MagicMock, patch

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


def test_memory_on_event_exception_handling(memory, event_stream):
    """Test that exceptions in Memory.on_event are properly handled and propagate to the agent controller."""
    # Mock the agent controller's _reset method to verify it's called
    with patch(
        'openhands.controller.agent_controller.AgentController._reset'
    ) as mock_reset:
        # Create a mock event stream that will propagate the error
        mock_event_stream = MagicMock()
        mock_event_stream.add_event.side_effect = Exception('Test error')

        # Create a memory instance with the mock event stream
        memory = Memory(mock_event_stream, 'test_sid')

        # Create a recall action
        recall_action = AgentRecallAction(query='test query')
        recall_action._source = EventSource.USER

        # This should raise the exception
        with pytest.raises(Exception) as exc_info:
            memory.on_event(recall_action)

        assert str(exc_info.value) == 'Test error'

        # Verify that the agent controller's reset was called
        mock_reset.assert_called_once()


def test_memory_on_first_recall_action_exception_handling(memory, event_stream):
    """Test that exceptions in Memory._on_first_recall_action are properly handled and propagate to the agent controller."""
    # Mock the agent controller's _reset method to verify it's called
    with patch(
        'openhands.controller.agent_controller.AgentController._reset'
    ) as mock_reset:
        # Create a mock event stream
        mock_event_stream = MagicMock()

        # Create a memory instance with the mock event stream
        memory = Memory(mock_event_stream, 'test_sid')

        # Mock _on_first_recall_action to raise an exception
        with patch.object(
            memory,
            '_on_first_recall_action',
            side_effect=Exception('Test error from _on_first_recall_action'),
        ):
            # Create a recall action that will trigger _on_first_recall_action
            recall_action = AgentRecallAction(query='test query')
            recall_action._source = EventSource.USER
            recall_action._id = 1  # This will make it the first message

            # Add a MessageAction with id=0 to make this the first user message
            message_action = MessageAction(content='test')
            message_action._source = EventSource.USER
            message_action._id = 0
            mock_event_stream.get_events.return_value = [message_action]

            # This should raise the exception
            with pytest.raises(Exception) as exc_info:
                memory.on_event(recall_action)

            assert str(exc_info.value) == 'Test error from _on_first_recall_action'

            # Verify that the agent controller's reset was called
            mock_reset.assert_called_once()
