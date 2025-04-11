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
    return InMemoryFileStore({})


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


def test_memory_repository_info(prompt_dir, file_store):
    """Test that Memory adds repository info to RecallObservations."""
    # real event stream
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


@pytest.mark.asyncio
async def test_memory_with_agent_microagents():
    """
    Test that Memory processes microagent based on trigger words from agent messages.
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

    # Set the source to AGENT
    microagent_action._source = EventSource.AGENT  # type: ignore[attr-defined]

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the microagent action to the event stream
    event_stream.add_event(microagent_action, EventSource.AGENT)

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


def test_memory_multiple_repo_microagents(prompt_dir, file_store):
    """Test that Memory loads and concatenates multiple repo microagents correctly."""
    # Create real event stream
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create two test repo microagents
    repo_microagent1_name = 'test_repo_microagent1'
    repo_microagent1_content = """---
REPOSITORY INSTRUCTIONS: This is the first test repository.
"""

    repo_microagent2_name = 'test_repo_microagent2'
    repo_microagent2_content = """---
name: test_repo2
type: repo
agent: CodeActAgent
---

REPOSITORY INSTRUCTIONS: This is the second test repository.
"""

    # Create temporary repo microagent files
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent1_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent1_content)

    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent2_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent2_content)

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

        # We should have one RecallObservation
        assert len(microagent_obs_events) > 0

        # Get the first RecallObservation
        observation = microagent_obs_events[0]
        assert observation.recall_type == RecallType.WORKSPACE_CONTEXT
        assert observation.repo_name == 'owner/repo'
        assert observation.repo_directory == '/workspace/repo'
        assert 'This is the first test repository' in observation.repo_instructions
        assert 'This is the second test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent1_name}.md'))
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent2_name}.md'))
