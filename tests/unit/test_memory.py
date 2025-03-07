import asyncio
import time
from unittest.mock import patch

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.events.action.agent import AgentRecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.llm.metrics import Metrics
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
    """Test that exceptions in Memory.on_event are properly handled via status callback."""

    # Create a dummy agent for the controller
    class DummyAgent:
        def __init__(self):
            self.name = 'dummy'
            self.llm = type(
                'DummyLLM',
                (),
                {'metrics': Metrics()},
            )()

        def reset(self):
            pass

    # Track status callback calls
    status_calls = []

    def status_callback(status_type: str, status_id: str, msg: str):
        status_calls.append((status_type, status_id, msg))

    # Set the status callback BEFORE creating the controller
    memory.status_callback = status_callback

    # Create an agent controller that shares the same event stream as memory
    controller = AgentController(
        agent=DummyAgent(),
        event_stream=event_stream,
        max_iterations=10,
        sid='test_sid',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a recall action
    recall_action = AgentRecallAction(query='test query')
    recall_action._source = EventSource.USER

    # Mock the event stream to raise an exception
    with patch.object(event_stream, 'add_event', side_effect=Exception('Test error')):
        # This should not raise the exception, but call the status callback
        memory.on_event(recall_action)

        # give it a little time
        time.sleep(0.1)

        # Verify that the status callback was called with the error
        assert len(status_calls) == 1
        status_type, status_id, msg = status_calls[0]
        assert status_type == 'error'
        assert status_id == 'STATUS$ERROR_MEMORY'
        assert 'Error: Exception' in msg

        assert controller._pending_action is None

    # Clean up
    asyncio.get_event_loop().run_until_complete(controller.close())


def test_memory_on_first_recall_action_exception_handling(memory, event_stream):
    """Test that exceptions in Memory._on_first_recall_action are properly handled via status callback."""

    # Create a dummy agent for the controller
    class DummyAgent:
        def __init__(self):
            self.name = 'dummy'
            self.llm = type(
                'DummyLLM',
                (),
                {'metrics': Metrics()},
            )()

        def reset(self):
            pass

    # Track status callback calls
    status_calls = []

    def status_callback(status_type: str, status_id: str, msg: str):
        status_calls.append((status_type, status_id, msg))

    # Set the status callback before creating the controller
    memory.status_callback = status_callback

    # Create an agent controller that shares the same event stream as memory
    controller = AgentController(
        agent=DummyAgent(),
        event_stream=event_stream,
        max_iterations=10,
        sid='test_sid',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.status_callback = status_callback

    # Add a MessageAction to make this the first user message
    message_action = MessageAction(content='test')
    message_action._source = EventSource.USER
    event_stream.add_event(message_action, EventSource.USER)

    # Create a recall action that will trigger _on_first_recall_action
    recall_action = AgentRecallAction(query='test query')
    recall_action._source = EventSource.USER
    event_stream.add_event(recall_action, EventSource.USER)

    # Mock the event stream to raise an exception
    with patch.object(
        event_stream,
        'add_event',
        side_effect=Exception('Test error from _on_first_recall_action'),
    ):
        # This should not raise the exception, but call the status callback
        memory.on_event(recall_action)

        # give it a little time
        time.sleep(0.1)

        # Verify that the status callback was called with the error
        assert len(status_calls) == 1
        status_type, status_id, msg = status_calls[0]
        assert status_type == 'error'
        assert status_id == 'STATUS$ERROR_MEMORY'
        assert 'Error: Exception' in msg

        assert controller._pending_action is None

    # Clean up
    asyncio.get_event_loop().run_until_complete(controller.close())
