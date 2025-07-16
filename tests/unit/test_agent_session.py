from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import LLMConfig, OpenHandsConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.events import EventStream, EventStreamSubscriber
from openhands.integrations.service_types import ProviderType
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
async def test_metrics_centralization_and_sharing(mock_agent):
    """Test that metrics are centralized and shared between controller and agent."""

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

    # Create a real Memory instance with the mock event stream
    memory = Memory(event_stream=mock_event_stream, sid='test-session')
    memory.microagents_dir = 'test-dir'

    # Patch necessary components
    with (
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

        # Verify that the agent's LLM metrics and controller's state metrics are the same object
        assert session.controller.agent.llm.metrics is session.controller.state.metrics

        # Add some metrics to the agent's LLM
        test_cost = 0.05
        session.controller.agent.llm.metrics.add_cost(test_cost)

        # Verify that the cost is reflected in the controller's state metrics
        assert session.controller.state.metrics.accumulated_cost == test_cost

        # Create a test metrics object to simulate an observation with metrics
        test_observation_metrics = Metrics()
        test_observation_metrics.add_cost(0.1)

        # Get the current accumulated cost before merging
        current_cost = session.controller.state.metrics.accumulated_cost

        # Simulate merging metrics from an observation
        session.controller.state_tracker.merge_metrics(test_observation_metrics)

        # Verify that the merged metrics are reflected in both agent and controller
        assert session.controller.state.metrics.accumulated_cost == current_cost + 0.1
        assert (
            session.controller.agent.llm.metrics.accumulated_cost == current_cost + 0.1
        )

        # Reset the agent and verify that metrics are not reset
        session.controller.agent.reset()

        # Metrics should still be the same after reset
        assert session.controller.state.metrics.accumulated_cost == test_cost + 0.1
        assert session.controller.agent.llm.metrics.accumulated_cost == test_cost + 0.1
        assert session.controller.agent.llm.metrics is session.controller.state.metrics


@pytest.mark.asyncio
async def test_budget_control_flag_syncs_with_metrics(mock_agent):
    """Test that BudgetControlFlag's current value matches the accumulated costs."""

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

    # Create a real Memory instance with the mock event stream
    memory = Memory(event_stream=mock_event_stream, sid='test-session')
    memory.microagents_dir = 'test-dir'

    # Patch necessary components
    with (
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
        # Start the session with a budget limit
        await session.start(
            runtime_name='test-runtime',
            config=OpenHandsConfig(),
            agent=mock_agent,
            max_iterations=10,
            max_budget_per_task=1.0,  # Set a budget limit
        )

        # Verify that the budget control flag was created
        assert session.controller.state.budget_flag is not None
        assert session.controller.state.budget_flag.max_value == 1.0
        assert session.controller.state.budget_flag.current_value == 0.0

        # Add some metrics to the agent's LLM
        test_cost = 0.05
        session.controller.agent.llm.metrics.add_cost(test_cost)

        # Verify that the budget control flag's current value is updated
        # This happens through the state_tracker.sync_budget_flag_with_metrics method
        session.controller.state_tracker.sync_budget_flag_with_metrics()
        assert session.controller.state.budget_flag.current_value == test_cost

        # Create a test metrics object to simulate an observation with metrics
        test_observation_metrics = Metrics()
        test_observation_metrics.add_cost(0.1)

        # Simulate merging metrics from an observation
        session.controller.state_tracker.merge_metrics(test_observation_metrics)

        # Verify that the budget control flag's current value is updated to match the new accumulated cost
        assert session.controller.state.budget_flag.current_value == test_cost + 0.1

        # Reset the agent and verify that metrics and budget flag are not reset
        session.controller.agent.reset()

        # Budget control flag should still reflect the accumulated cost after reset
        assert session.controller.state.budget_flag.current_value == test_cost + 0.1


def test_override_provider_tokens_with_custom_secret():
    """Test that override_provider_tokens_with_custom_secret works correctly.

    This test verifies that the method properly removes provider tokens when
    corresponding custom secrets exist, without causing the 'dictionary changed
    size during iteration' error that occurred before the fix.
    """
    # Setup
    file_store = InMemoryFileStore({})
    session = AgentSession(
        sid='test-session',
        file_store=file_store,
    )

    # Create test data
    git_provider_tokens = {
        ProviderType.GITHUB: 'github_token_123',
        ProviderType.GITLAB: 'gitlab_token_456',
        ProviderType.BITBUCKET: 'bitbucket_token_789',
    }

    # Custom secrets that will cause some providers to be removed
    # Tests both lowercase and uppercase variants to ensure comprehensive coverage
    custom_secrets = {
        'github_token': 'custom_github_token',
        'GITLAB_TOKEN': 'custom_gitlab_token',
    }

    # This should work without raising RuntimeError: dictionary changed size during iteration
    result = session.override_provider_tokens_with_custom_secret(
        git_provider_tokens, custom_secrets
    )

    # Verify that GitHub and GitLab tokens were removed (they have custom secrets)
    assert ProviderType.GITHUB not in result
    assert ProviderType.GITLAB not in result

    # Verify that Bitbucket token remains (no custom secret for it)
    assert ProviderType.BITBUCKET in result
    assert result[ProviderType.BITBUCKET] == 'bitbucket_token_789'
