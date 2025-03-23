from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import AppConfig, LLMConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.events import EventStream, EventStreamSubscriber
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime
from openhands.server.session.agent_session import AgentSession
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_agent():
    """Create a properly configured mock agent with all required nested attributes"""
    # Create the base mocks
    agent = MagicMock(spec=Agent)
    llm = MagicMock(spec=LLM)
    metrics = MagicMock(spec=Metrics)
    llm_config = MagicMock(spec=LLMConfig)
    agent_config = MagicMock(spec=AgentConfig)

    # Configure the LLM config
    llm_config.model = 'test-model'
    llm_config.base_url = 'http://test'
    llm_config.max_message_chars = 1000

    # Configure the agent config
    agent_config.disabled_microagents = []

    # Set up the chain of mocks
    llm.metrics = metrics
    llm.config = llm_config
    agent.llm = llm
    agent.name = 'test-agent'
    agent.sandbox_plugins = []
    agent.config = agent_config
    agent.prompt_manager = MagicMock()

    return agent


@pytest.mark.asyncio
async def test_agent_session_start_with_no_state(mock_agent):
    """Test that AgentSession.start() works correctly when there's no state to restore"""

    # Setup
    file_store = InMemoryFileStore({})
    session = AgentSession(
        sid='test-session',
        file_store=file_store,
    )

    # Create a mock runtime and set it up
    mock_runtime = MagicMock(spec=Runtime)

    # Mock the runtime creation to set up the runtime attribute
    async def mock_create_runtime(*args, **kwargs):
        session.runtime = mock_runtime
        return True

    session._create_runtime = AsyncMock(side_effect=mock_create_runtime)

    # Create a mock EventStream with no events
    mock_event_stream = MagicMock(spec=EventStream)
    mock_event_stream.get_events.return_value = []
    mock_event_stream.subscribe = MagicMock()
    mock_event_stream.get_latest_event_id.return_value = 0

    # Inject the mock event stream into the session
    session.event_stream = mock_event_stream

    # Create a spy on set_initial_state
    class SpyAgentController(AgentController):
        set_initial_state_call_count = 0
        test_initial_state = None

        def set_initial_state(self, *args, state=None, **kwargs):
            self.set_initial_state_call_count += 1
            self.test_initial_state = state
            super().set_initial_state(*args, state=state, **kwargs)

    # Create a real Memory instance with the mock event stream
    memory = Memory(event_stream=mock_event_stream, sid='test-session')
    memory.microagents_dir = 'test-dir'

    # Patch AgentController and State.restore_from_session to fail; patch Memory in AgentSession
    with patch(
        'openhands.server.session.agent_session.AgentController', SpyAgentController
    ), patch(
        'openhands.server.session.agent_session.EventStream',
        return_value=mock_event_stream,
    ), patch(
        'openhands.controller.state.state.State.restore_from_session',
        side_effect=Exception('No state found'),
    ), patch('openhands.server.session.agent_session.Memory', return_value=memory):
        await session.start(
            runtime_name='test-runtime',
            config=AppConfig(),
            agent=mock_agent,
            max_iterations=10,
        )

        # Verify EventStream.subscribe was called with correct parameters
        mock_event_stream.subscribe.assert_any_call(
            EventStreamSubscriber.AGENT_CONTROLLER,
            session.controller.on_event,
            session.controller.id,
        )

        mock_event_stream.subscribe.assert_any_call(
            EventStreamSubscriber.MEMORY,
            session.memory.on_event,
            session.controller.id,
        )

        # Verify set_initial_state was called once with None as state
        assert session.controller.set_initial_state_call_count == 1
        assert session.controller.test_initial_state is None
        assert session.controller.state.max_iterations == 10
        assert session.controller.agent.name == 'test-agent'
        assert session.controller.state.start_id == 0
        assert session.controller.state.end_id == -1
        assert session.controller.state.truncation_id == -1


@pytest.mark.asyncio
async def test_agent_session_start_with_restored_state(mock_agent):
    """Test that AgentSession.start() works correctly when there's a state to restore"""

    # Setup
    file_store = InMemoryFileStore({})
    session = AgentSession(
        sid='test-session',
        file_store=file_store,
    )

    # Create a mock runtime and set it up
    mock_runtime = MagicMock(spec=Runtime)

    # Mock the runtime creation to set up the runtime attribute
    async def mock_create_runtime(*args, **kwargs):
        session.runtime = mock_runtime
        return True

    session._create_runtime = AsyncMock(side_effect=mock_create_runtime)

    # Create a mock EventStream with some events
    mock_event_stream = MagicMock(spec=EventStream)
    mock_event_stream.get_events.return_value = []
    mock_event_stream.subscribe = MagicMock()
    mock_event_stream.get_latest_event_id.return_value = 5  # Indicate some events exist

    # Inject the mock event stream into the session
    session.event_stream = mock_event_stream

    # Create a mock restored state
    mock_restored_state = MagicMock(spec=State)
    mock_restored_state.start_id = -1
    mock_restored_state.end_id = -1
    mock_restored_state.truncation_id = -1
    mock_restored_state.max_iterations = 5

    # Create a spy on set_initial_state by subclassing AgentController
    class SpyAgentController(AgentController):
        set_initial_state_call_count = 0
        test_initial_state = None

        def set_initial_state(self, *args, state=None, **kwargs):
            self.set_initial_state_call_count += 1
            self.test_initial_state = state
            super().set_initial_state(*args, state=state, **kwargs)

    # create a mock Memory
    mock_memory = MagicMock(spec=Memory)

    # Patch AgentController and State.restore_from_session to succeed, patch Memory in AgentSession
    with patch(
        'openhands.server.session.agent_session.AgentController', SpyAgentController
    ), patch(
        'openhands.server.session.agent_session.EventStream',
        return_value=mock_event_stream,
    ), patch(
        'openhands.controller.state.state.State.restore_from_session',
        return_value=mock_restored_state,
    ), patch('openhands.server.session.agent_session.Memory', mock_memory):
        await session.start(
            runtime_name='test-runtime',
            config=AppConfig(),
            agent=mock_agent,
            max_iterations=10,
        )

        # Verify set_initial_state was called once with the restored state
        assert session.controller.set_initial_state_call_count == 1

        # Verify EventStream.subscribe was called with correct parameters
        mock_event_stream.subscribe.assert_called_with(
            EventStreamSubscriber.AGENT_CONTROLLER,
            session.controller.on_event,
            session.controller.id,
        )
        assert session.controller.test_initial_state is mock_restored_state
        assert session.controller.state is mock_restored_state
        assert session.controller.state.max_iterations == 5
        assert session.controller.state.start_id == 0
        assert session.controller.state.end_id == -1
        assert session.controller.state.truncation_id == -1
