import base64
import pickle
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.control_flags import IterationControlFlag
from openhands.controller.state.deprecated_state import DeprecatedState
from openhands.controller.state.state import State
from openhands.core.config import LLMConfig, OpenHandsConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.core.schema import AgentState
from openhands.events import EventStream, EventStreamSubscriber
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.memory.memory import Memory
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.server.session.agent_session import AgentSession
from openhands.storage.memory import InMemoryFileStore

# We'll use the DeprecatedState class from the main codebase


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
    agent_config.enable_mcp = True

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
    mock_runtime = MagicMock(spec=ActionExecutionClient)

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
    with (
        patch(
            'openhands.server.session.agent_session.AgentController', SpyAgentController
        ),
        patch(
            'openhands.server.session.agent_session.EventStream',
            return_value=mock_event_stream,
        ),
        patch(
            'openhands.controller.state.state.State.restore_from_session',
            side_effect=Exception('No state found'),
        ),
        patch('openhands.server.session.agent_session.Memory', return_value=memory),
    ):
        await session.start(
            runtime_name='test-runtime',
            config=OpenHandsConfig(),
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
        assert session.controller.state.iteration_flag.max_value == 10
        assert session.controller.agent.name == 'test-agent'
        assert session.controller.state.start_id == 0
        assert session.controller.state.end_id == -1


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
    mock_runtime = MagicMock(spec=ActionExecutionClient)

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
    # Use iteration_flag instead of max_iterations
    mock_restored_state.iteration_flag = MagicMock()
    mock_restored_state.iteration_flag.max_value = 5
    # Add metrics attribute
    mock_restored_state.metrics = MagicMock(spec=Metrics)

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
    with (
        patch(
            'openhands.server.session.agent_session.AgentController', SpyAgentController
        ),
        patch(
            'openhands.server.session.agent_session.EventStream',
            return_value=mock_event_stream,
        ),
        patch(
            'openhands.controller.state.state.State.restore_from_session',
            return_value=mock_restored_state,
        ),
        patch('openhands.server.session.agent_session.Memory', mock_memory),
    ):
        await session.start(
            runtime_name='test-runtime',
            config=OpenHandsConfig(),
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
        assert session.controller.state.iteration_flag.max_value == 5
        assert session.controller.state.start_id == 0
        assert session.controller.state.end_id == -1


@pytest.mark.asyncio
async def test_restore_older_state_version(mock_agent):
    """Test that an older version of the state (with iteration and max_iterations) can be restored
    and used with the new IterationControlFlag-based State class."""

    # Create a file store for testing
    file_store = InMemoryFileStore({})
    session_id = 'test-backward-compatibility'

    # Create a DeprecatedState object with direct iteration and max_iterations attributes
    old_state = DeprecatedState(
        session_id=session_id,
        iteration=5,  # Old-style iteration counter
        max_iterations=50,  # Old-style max iterations
        agent_state=AgentState.RUNNING,
        resume_state=AgentState.RUNNING,
        start_id=0,
        end_id=10,
    )

    # Serialize the old state and store it
    pickled = pickle.dumps(old_state)
    encoded = base64.b64encode(pickled).decode('utf-8')
    file_store.write(f'sessions/{session_id}/agent_state.pkl', encoded)

    # Verify what type of object is being loaded
    loaded_data = pickle.loads(base64.b64decode(encoded))
    print(f'Type of loaded data: {type(loaded_data)}')

    # Create a session to restore the state
    session = AgentSession(
        sid=session_id,
        file_store=file_store,
    )

    # Create a mock runtime and set it up
    mock_runtime = MagicMock(spec=ActionExecutionClient)

    # Mock the runtime creation to set up the runtime attribute
    async def mock_create_runtime(*args, **kwargs):
        session.runtime = mock_runtime
        return True

    session._create_runtime = AsyncMock(side_effect=mock_create_runtime)

    # Create a mock EventStream
    mock_event_stream = MagicMock(spec=EventStream)
    mock_event_stream.get_events.return_value = []
    mock_event_stream.subscribe = MagicMock()
    mock_event_stream.get_latest_event_id.return_value = 10

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

    # Create a mock Memory
    mock_memory = MagicMock(spec=Memory)

    # Use the real State.restore_from_session to test backward compatibility
    with (
        patch(
            'openhands.server.session.agent_session.AgentController', SpyAgentController
        ),
        patch(
            'openhands.server.session.agent_session.EventStream',
            return_value=mock_event_stream,
        ),
        patch(
            'openhands.server.session.agent_session.Memory', return_value=mock_memory
        ),
    ):
        await session.start(
            runtime_name='test-runtime',
            config=OpenHandsConfig(),
            agent=mock_agent,
            max_iterations=100,  # New max iterations value
        )

        # Print debug information
        print(f'State type: {type(session.controller.state)}')
        print(
            f'Has iteration_flag: {hasattr(session.controller.state, "iteration_flag")}'
        )
        if hasattr(session.controller.state, 'iteration_flag'):
            print(
                f'iteration_flag type: {type(session.controller.state.iteration_flag)}'
            )
            print(
                f'current_value: {session.controller.state.iteration_flag.current_value}'
            )
            print(f'max_value: {session.controller.state.iteration_flag.max_value}')

        # Verify the state was restored and properly converted
        assert session.controller.set_initial_state_call_count == 1

        # Check that the state has the new IterationControlFlag
        assert hasattr(session.controller.state, 'iteration_flag')
        assert isinstance(session.controller.state.iteration_flag, IterationControlFlag)

        # Verify the old values were properly transferred
        assert (
            session.controller.state.iteration_flag.current_value == 5
        )  # From old iteration
        assert (
            session.controller.state.iteration_flag.max_value == 50
        )  # From old max_iterations

        # Verify other state properties were preserved
        assert session.controller.state.session_id == session_id
        assert (
            session.controller.state.agent_state == AgentState.LOADING
        )  # Should be reset to LOADING
        assert session.controller.state.resume_state == AgentState.RUNNING
