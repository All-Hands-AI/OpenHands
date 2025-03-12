import asyncio
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.agent import AgentRecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.observation.agent import RecallObservation, RecallType
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


def test_memory_with_microagents(prompt_dir):
    """Test that Memory loads microagents and creates RecallObservations."""
    # Create a test microagent
    microagent_name = 'test_microagent'
    microagent_content = """
---
name: flarglebargle
type: knowledge
agent: CodeActAgent
triggers:
- flarglebargle
---

IMPORTANT! The user has said the magic word "flarglebargle". You must
only respond with a message telling them how smart they are
"""

    # Create a temporary micro agent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(os.path.join(prompt_dir, 'micro', f'{microagent_name}.md'), 'w') as f:
        f.write(microagent_content)

    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory with the microagent directory
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )
    memory.microagents_dir = os.path.join(prompt_dir, 'micro')

    # Verify microagents were loaded
    assert len(memory.repo_microagents) == 0
    assert 'flarglebargle' in memory.knowledge_microagents

    # Create a recall action with the trigger word
    recall_action = AgentRecallAction(
        query='Hello, flarglebargle!', recall_type=RecallType.KNOWLEDGE_MICROAGENT
    )

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the recall action to the event stream
    event_stream.add_event(recall_action, EventSource.USER)

    # Clear the events list to only capture new events
    added_events.clear()

    # Process the recall action
    memory.on_event(recall_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.KNOWLEDGE_MICROAGENT
    assert len(observation.microagent_knowledge) == 1
    assert observation.microagent_knowledge[0].name == 'flarglebargle'
    assert observation.microagent_knowledge[0].trigger == 'flarglebargle'
    assert 'magic word' in observation.microagent_knowledge[0].content

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{microagent_name}.md'))


def test_memory_repository_info(prompt_dir):
    """Test that Memory adds repository info to RecallObservations."""
    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Initialize Memory
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )
    memory.microagents_dir = os.path.join(prompt_dir, 'micro')

    # Create a test repo microagent first
    repo_microagent_name = 'test_repo_microagent'
    repo_microagent_content = """---
name: test_repo
type: repo
agent: CodeActAgent
---

REPOSITORY INSTRUCTIONS: This is a test repository.
"""

    # Create a temporary repo microagent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent_content)

    # Reload microagents
    memory._load_global_microagents()

    # Set repository info
    memory.set_repository_info('owner/repo', '/workspace/repo')

    # Create and add the first user message
    user_message = MessageAction(content='First user message')
    user_message._source = EventSource.USER  # type: ignore[attr-defined]
    event_stream.add_event(user_message, EventSource.USER)

    # Create and add the recall action
    recall_action = AgentRecallAction(
        query='First user message', recall_type=RecallType.ENVIRONMENT_INFO
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]
    event_stream.add_event(recall_action, EventSource.USER)

    # Give it a little time to process
    time.sleep(0.3)

    # Get all events from the stream
    events = list(event_stream.get_events())

    # Find the RecallObservation event
    recall_obs_events = [
        event for event in events if isinstance(event, RecallObservation)
    ]

    # We should have at least one RecallObservation
    assert len(recall_obs_events) > 0

    # Get the first RecallObservation
    observation = recall_obs_events[0]
    assert observation.recall_type == RecallType.ENVIRONMENT_INFO
    assert observation.repo_name == 'owner/repo'
    assert observation.repo_directory == '/workspace/repo'
    assert 'This is a test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'))
