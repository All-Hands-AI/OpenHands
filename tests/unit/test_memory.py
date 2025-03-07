import asyncio
from unittest.mock import MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.agent import AgentRecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.stream import EventStream
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    memory = Memory(event_stream, 'test_sid')
    yield memory
    loop.close()


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


@pytest.mark.asyncio
async def test_memory_on_event_exception_handling(memory, event_stream):
    """Test that exceptions in Memory.on_event are properly handled via status callback."""

    # Create a dummy agent for the controller
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = AppConfig().get_llm_config()

    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream

    # Mock Memory method to raise an exception
    with patch.object(
        memory, '_on_first_recall_action', side_effect=Exception('Test error')
    ):
        state = await run_controller(
            config=AppConfig(),
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            agent=agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=memory,
        )

        # Verify that the controller's last error was set
        assert state.iteration == 0
        assert state.agent_state == AgentState.ERROR
        assert state.last_error == 'Error: Exception'


@pytest.mark.asyncio
async def test_memory_on_first_recall_action_exception_handling(memory, event_stream):
    """Test that exceptions in Memory._on_first_recall_action are properly handled via status callback."""

    # Create a dummy agent for the controller
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = AppConfig().get_llm_config()

    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream

    # Mock Memory._on_first_recall_action to raise an exception
    with patch.object(
        memory,
        '_on_first_recall_action',
        side_effect=Exception('Test error from _on_first_recall_action'),
    ):
        state = await run_controller(
            config=AppConfig(),
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            agent=agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=memory,
        )

        # Verify that the controller's last error was set
        assert state.iteration == 0
        assert state.agent_state == AgentState.ERROR
        assert state.last_error == 'Error: Exception'
