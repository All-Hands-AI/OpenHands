import asyncio
import os
import shutil
import time
from unittest.mock import MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.observation.agent import (
    RecallObservation,
    RecallType,
)
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


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


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
        memory, '_on_workspace_context_recall', side_effect=Exception('Test error')
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
async def test_memory_on_workspace_context_recall_exception_handling(
    memory, event_stream
):
    """Test that exceptions in Memory._on_workspace_context_recall are properly handled via status callback."""
    # Create a dummy agent for the controller
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = AppConfig().get_llm_config()

    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream

    # Mock Memory._on_workspace_context_recall to raise an exception
    with patch.object(
        memory,
        '_find_microagent_knowledge',
        side_effect=Exception('Test error from _find_microagent_knowledge'),
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
async def test_memory_with_microagents():
    """Test that Memory loads microagents from the global directory and processes microagent actions.

    This test verifies that:
    1. Memory loads microagents from the global GLOBAL_MICROAGENTS_DIR
    2. When a microagent action with a trigger word is processed, a RecallObservation is created
    """
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory to use the global microagents dir
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )

    # Verify microagents were loaded - at least one microagent should be loaded
    # from the global directory that's in the repo
    assert len(memory.knowledge_microagents) > 0

    # We know 'flarglebargle' exists in the global directory
    assert 'flarglebargle' in memory.knowledge_microagents

    # Create a microagent action with the trigger word
    microagent_action = RecallAction(
        query='Hello, flarglebargle!', recall_type=RecallType.KNOWLEDGE
    )

    # Set the source to USER
    microagent_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the microagent action to the event stream
    event_stream.add_event(microagent_action, EventSource.USER)

    # Clear the events list to only capture new events
    added_events.clear()

    # Process the microagent action
    await memory._on_event(microagent_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.KNOWLEDGE
    assert len(observation.microagent_knowledge) == 1
    assert observation.microagent_knowledge[0].name == 'flarglebargle'
    assert observation.microagent_knowledge[0].trigger == 'flarglebargle'
    assert 'magic word' in observation.microagent_knowledge[0].content


def test_memory_repository_info(prompt_dir):
    """Test that Memory adds repository info to RecallObservations."""
    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

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

    # Patch the global microagents directory to use our test directory
    test_microagents_dir = os.path.join(prompt_dir, 'micro')
    with patch('openhands.memory.memory.GLOBAL_MICROAGENTS_DIR', test_microagents_dir):
        # Initialize Memory
        memory = Memory(
            event_stream=event_stream,
            sid='test-session',
        )

        # Set repository info
        memory.set_repository_info('owner/repo', '/workspace/repo')

        # Create and add the first user message
        user_message = MessageAction(content='First user message')
        user_message._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(user_message, EventSource.USER)

        # Create and add the microagent action
        microagent_action = RecallAction(
            query='First user message', recall_type=RecallType.WORKSPACE_CONTEXT
        )
        microagent_action._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(microagent_action, EventSource.USER)

        # Give it a little time to process
        time.sleep(0.3)

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Find the RecallObservation event
        microagent_obs_events = [
            event for event in events if isinstance(event, RecallObservation)
        ]

        # We should have at least one RecallObservation
        assert len(microagent_obs_events) > 0

        # Get the first RecallObservation
        observation = microagent_obs_events[0]
        assert observation.recall_type == RecallType.WORKSPACE_CONTEXT
        assert observation.repo_name == 'owner/repo'
        assert observation.repo_directory == '/workspace/repo'
        assert 'This is a test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'))


def test_agent_controller_should_step_with_null_observation_cause_zero():
    """Test that AgentController's should_step method returns False for NullObservation with cause = 0."""
    from unittest.mock import MagicMock

    from openhands.controller.agent import Agent
    from openhands.controller.agent_controller import AgentController
    from openhands.events.observation.empty import NullObservation

    # Create a mock event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create a mock agent
    mock_agent = MagicMock(spec=Agent)

    # Create an agent controller
    controller = AgentController(
        agent=mock_agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='test-session',
    )

    # Create a NullObservation with cause = 0
    null_observation = NullObservation(content='Test observation')
    null_observation._cause = 0  # type: ignore[attr-defined]

    # Check if should_step returns False for this observation
    result = controller.should_step(null_observation)

    # It should return False since we only want to step on NullObservation with cause > 0
    assert (
        result is False
    ), 'should_step should return False for NullObservation with cause = 0'


@pytest.mark.asyncio
async def test_agent_controller_processes_null_observation_with_cause():
    """Test that AgentController processes NullObservation events with a cause value.

    And that the agent's step method is called as a result.
    """
    from unittest.mock import MagicMock, patch

    from openhands.controller.agent import Agent
    from openhands.controller.agent_controller import AgentController
    from openhands.events.action.agent import RecallAction
    from openhands.events.observation.empty import NullObservation

    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create a Memory instance
    memory = Memory(event_stream=event_stream, sid='test-session')

    # Create a mock agent with necessary attributes
    mock_agent = MagicMock(spec=Agent)
    mock_agent.llm = MagicMock(spec=LLM)
    mock_agent.llm.metrics = Metrics()
    mock_agent.llm.config = AppConfig().get_llm_config()

    # Create a controller with the mock agent
    controller = AgentController(
        agent=mock_agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='test-session',
    )

    # Patch the controller's step method to track calls
    with patch.object(controller, 'step') as mock_step:
        # Create and add the first user message (will have ID 0)
        user_message = MessageAction(content='First user message')
        user_message._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(user_message, EventSource.USER)

        # Give it a little time to process
        await asyncio.sleep(0.3)

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Print all events for debugging
        print('\n=== EVENTS IN STREAM ===')
        for i, event in enumerate(events):
            event_type = type(event).__name__
            event_id = event.id
            event_cause = getattr(event, 'cause', 'N/A')
            event_content = getattr(event, 'content', 'N/A')
            event_source = getattr(event, 'source', 'N/A')
            print(
                f'Event {i}: {event_type}, ID: {event_id}, Cause: {event_cause}, Source: {event_source}'
            )
            print(
                f'  Content: {event_content[:100]}...'
                if len(str(event_content)) > 100
                else f'  Content: {event_content}'
            )
        print('=== END EVENTS ===\n')

        # Find the RecallAction event (should be automatically created)
        recall_actions = [event for event in events if isinstance(event, RecallAction)]
        assert len(recall_actions) > 0, 'No RecallAction was created'
        recall_action = recall_actions[0]

        # Find any NullObservation events
        null_obs_events = [
            event for event in events if isinstance(event, NullObservation)
        ]
        assert len(null_obs_events) > 0, 'No NullObservation was created'
        null_observation = null_obs_events[0]

        # Verify the NullObservation has a cause that points to a RecallAction
        assert null_observation.cause is not None, 'NullObservation cause is None'
        # The cause might not point to the first RecallAction, but it should point to some RecallAction
        assert (
            null_observation.cause > 0
        ), f'Expected cause > 0, got cause={null_observation.cause}'

        # Verify the controller's should_step method returns True for this observation
        assert controller.should_step(
            null_observation
        ), 'should_step should return True for this NullObservation'

        # Verify the controller's step method was called
        # This means the controller processed the NullObservation
        assert mock_step.called, "Controller's step method was not called"

        # Now test with a NullObservation that has cause=0
        # Create a NullObservation with cause = 0 (pointing to the first user message)
        null_observation_zero = NullObservation(content='Test observation with cause=0')
        null_observation_zero._cause = 0  # type: ignore[attr-defined]

        # Verify the controller's should_step method would return False for this observation
        assert not controller.should_step(
            null_observation_zero
        ), 'should_step should return False for NullObservation with cause=0'
