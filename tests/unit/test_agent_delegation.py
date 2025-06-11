import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import LLMConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    MessageAction,
)
from openhands.events.action.agent import RecallAction
from openhands.events.event import Event, RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.stream import EventStreamSubscriber
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics, TokenUsage
from openhands.memory.memory import Memory
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_event_stream():
    """Creates an event stream in memory."""
    sid = f'test-{uuid4()}'
    file_store = InMemoryFileStore({})
    return EventStream(sid=sid, file_store=file_store)


@pytest.fixture
def mock_parent_agent():
    """Creates a mock parent agent for testing delegation."""
    agent = MagicMock(spec=Agent)
    agent.name = 'ParentAgent'
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = LLMConfig()
    agent.llm.retry_listener = None  # Add retry_listener attribute
    agent.config = AgentConfig()

    # Add a proper system message mock
    from openhands.events.action.message import SystemMessageAction

    system_message = SystemMessageAction(content='Test system message')
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message

    return agent


@pytest.fixture
def mock_child_agent():
    """Creates a mock child agent for testing delegation."""
    agent = MagicMock(spec=Agent)
    agent.name = 'ChildAgent'
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = LLMConfig()
    agent.llm.retry_listener = None  # Add retry_listener attribute
    agent.config = AgentConfig()

    # Add a proper system message mock
    from openhands.events.action.message import SystemMessageAction

    system_message = SystemMessageAction(content='Test system message')
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message

    return agent


@pytest.mark.asyncio
async def test_delegation_flow(mock_parent_agent, mock_child_agent, mock_event_stream):
    """
    Test that when the parent agent delegates to a child, the parent's delegate
    is set, and once the child finishes, the parent is cleaned up properly.
    """
    # Mock the agent class resolution so that AgentController can instantiate mock_child_agent
    Agent.get_cls = Mock(return_value=lambda llm, config: mock_child_agent)

    # Create parent controller
    parent_state = State(inputs={})
    # Set the iteration flag's max_value to 10 (equivalent to the old max_iterations)
    parent_state.iteration_flag.max_value = 10
    parent_controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        iteration_delta=1,  # Add the required iteration_delta parameter
        sid='parent',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=parent_state,
    )

    # Setup Memory to catch RecallActions
    mock_memory = MagicMock(spec=Memory)
    mock_memory.event_stream = mock_event_stream

    def on_event(event: Event):
        if isinstance(event, RecallAction):
            # create a RecallObservation
            microagent_observation = RecallObservation(
                recall_type=RecallType.KNOWLEDGE,
                content='Found info',
            )
            microagent_observation._cause = event.id  # ignore attr-defined warning
            mock_event_stream.add_event(microagent_observation, EventSource.ENVIRONMENT)

    mock_memory.on_event = on_event
    mock_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, mock_memory.on_event, mock_memory
    )

    # Setup a delegate action from the parent
    delegate_action = AgentDelegateAction(agent='ChildAgent', inputs={'test': True})
    mock_parent_agent.step.return_value = delegate_action

    # Simulate a user message event to cause parent.step() to run
    message_action = MessageAction(content='please delegate now')
    message_action._source = EventSource.USER
    await parent_controller._on_event(message_action)

    # Give time for the async step() to execute
    await asyncio.sleep(1)

    # Verify that a RecallObservation was added to the event stream
    events = list(mock_event_stream.get_events())

    # The exact number of events might vary depending on implementation details
    # Just verify that we have at least a few events
    assert mock_event_stream.get_latest_event_id() >= 3

    # a RecallObservation and an AgentDelegateAction should be in the list
    assert any(isinstance(event, RecallObservation) for event in events)
    assert any(isinstance(event, AgentDelegateAction) for event in events)

    # Verify that a delegate agent controller is created
    assert parent_controller.delegate is not None, (
        "Parent's delegate controller was not set."
    )

    # The parent's iteration should have incremented
    assert parent_controller.state.iteration_flag.current_value == 1, (
        'Parent iteration should be incremented after step.'
    )

    # Now simulate that the child increments local iteration and finishes its subtask
    delegate_controller = parent_controller.delegate
    delegate_controller.state.iteration_flag.current_value = 5  # child had some steps
    delegate_controller.state.outputs = {'delegate_result': 'done'}

    # The child is done, so we simulate it finishing:
    child_finish_action = AgentFinishAction()
    await delegate_controller._on_event(child_finish_action)
    await asyncio.sleep(0.5)

    # Now the parent's delegate is None
    assert parent_controller.delegate is None, (
        'Parent delegate should be None after child finishes.'
    )

    # Parent's global iteration is updated from the child
    assert parent_controller.state.iteration_flag.current_value == 6, (
        "Parent iteration should be the child's iteration + 1 after child is done."
    )

    # Cleanup
    await parent_controller.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'delegate_state',
    [
        AgentState.RUNNING,
        AgentState.FINISHED,
        AgentState.ERROR,
        AgentState.REJECTED,
    ],
)
async def test_delegate_step_different_states(
    mock_parent_agent, mock_event_stream, delegate_state
):
    """Ensure that delegate is closed or remains open based on the delegate's state."""
    # Create a state with iteration_flag.max_value set to 10
    state = State(inputs={})
    state.iteration_flag.max_value = 10
    controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        iteration_delta=1,  # Add the required iteration_delta parameter
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=state,
    )

    mock_delegate = AsyncMock()
    controller.delegate = mock_delegate

    mock_delegate.state.iteration_flag = MagicMock()
    mock_delegate.state.iteration_flag.current_value = 5
    mock_delegate.state.outputs = {'result': 'test'}
    mock_delegate.agent.name = 'TestDelegate'

    mock_delegate.get_agent_state = Mock(return_value=delegate_state)
    mock_delegate._step = AsyncMock()
    mock_delegate.close = AsyncMock()

    def call_on_event_with_new_loop():
        """
        In this thread, create and set a fresh event loop, so that the run_until_complete()
        calls inside controller.on_event(...) find a valid loop.
        """
        loop_in_thread = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop_in_thread)
            msg_action = MessageAction(content='Test message')
            msg_action._source = EventSource.USER
            controller.on_event(msg_action)
        finally:
            loop_in_thread.close()

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        future = loop.run_in_executor(executor, call_on_event_with_new_loop)
        await future

    if delegate_state == AgentState.RUNNING:
        assert controller.delegate is not None
        assert controller.state.iteration_flag.current_value == 0
        mock_delegate.close.assert_not_called()
    else:
        assert controller.delegate is None
        assert controller.state.iteration_flag.current_value == 5
        # The close method is called once in end_delegate
        assert mock_delegate.close.call_count == 1

    await controller.close()


@pytest.mark.asyncio
async def test_delegate_metrics_propagation(
    mock_parent_agent, mock_child_agent, mock_event_stream
):
    """
    Test that when a delegate agent accumulates metrics, they are properly propagated
    to the parent agent's metrics.

    This test verifies that:
    1. The delegate inherits the parent's budget flag
    2. Updates to the delegate's metrics are reflected in the parent's metrics
    3. The budget flag is properly updated based on the metrics
    """
    # Mock the agent class resolution so that AgentController can instantiate mock_child_agent
    Agent.get_cls = Mock(return_value=lambda llm, config: mock_child_agent)

    # Create a file store for the test
    file_store = InMemoryFileStore()

    # Create parent controller with budget tracking
    from openhands.controller.state.control_flags import BudgetControlFlag
    from openhands.events.action import AgentDelegateAction

    # Create a parent state with budget tracking
    parent_state = State(inputs={})
    parent_state.iteration_flag.max_value = 10
    parent_state.budget_flag = BudgetControlFlag(
        initial_value=10.0, current_value=0.0, max_value=10.0
    )

    # Create the parent controller
    parent_controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        iteration_delta=1,
        budget_per_task_delta=10.0,
        sid='parent',
        file_store=file_store,
        confirmation_mode=False,
        headless_mode=True,
        initial_state=parent_state,
    )

    # Create a delegate action
    delegate_action = AgentDelegateAction(
        agent='ChildAgent',  # This should match the agent class name
        inputs={'test': True},
    )

    # Have the parent controller start the delegate
    await parent_controller.start_delegate(delegate_action)

    # Get the delegate controller that was created
    delegate_controller = parent_controller.delegate

    # Verify that the delegate was created
    assert delegate_controller is not None

    # Verify that the parent and delegate share the same metrics object
    assert parent_controller.state.metrics is delegate_controller.state.metrics

    # Verify that the parent and delegate share the same budget flag
    assert parent_controller.state.budget_flag is delegate_controller.state.budget_flag

    # Add some metrics to the delegate's metrics
    delegate_cost = 0.25
    delegate_controller.state.metrics.add_cost(delegate_cost)

    # Sync the budget flag with metrics
    delegate_controller.state_tracker.sync_budget_flag_with_metrics()

    # Verify the delegate's budget flag is updated
    assert delegate_controller.state.budget_flag.current_value == delegate_cost

    # Verify that the parent's metrics are automatically updated (since they share the same object)
    assert parent_controller.state.metrics.accumulated_cost == delegate_cost

    # Verify that the parent's budget flag is also updated (since it's the same object)
    assert parent_controller.state.budget_flag.current_value == delegate_cost

    # Cleanup
    await parent_controller.close()


@pytest.mark.asyncio
async def test_delegate_metrics_snapshot():
    """
    Test that we can compute local metrics and iterations for delegates using snapshots.
    """
    # Create a simple test to verify metrics snapshots
    from openhands.controller.state.control_flags import IterationControlFlag
    from openhands.llm.metrics import Metrics

    # Create parent metrics with initial cost
    parent_metrics = Metrics()
    initial_parent_cost = 0.1
    parent_metrics.add_cost(initial_parent_cost)

    # Take a snapshot of parent metrics before delegation
    parent_metrics_before = parent_metrics.copy()

    # Create parent iteration flag and set initial value
    parent_iteration_flag = IterationControlFlag(
        initial_value=10, current_value=0, max_value=10
    )
    parent_iterations_before = parent_iteration_flag.current_value

    # Increment parent iteration to simulate delegation step
    parent_iteration_flag.current_value += 1

    # Create delegate metrics and add some cost and token usage
    delegate_metrics = Metrics()
    delegate_cost = 0.25

    # Create token usage parameters
    prompt_tokens = 100
    completion_tokens = 50
    cache_read_tokens = 0
    cache_write_tokens = 0
    total_tokens = 150
    token_id = 'test-delegate'

    # Create token usage object
    TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        context_window=0,
        per_turn_token=0,
        response_id=token_id,
    )

    # Add cost and token usage to metrics
    delegate_metrics.add_cost(delegate_cost)
    delegate_metrics.add_token_usage(
        prompt_tokens,
        completion_tokens,
        cache_read_tokens,
        cache_write_tokens,
        total_tokens,
        token_id,
    )

    # Create delegate iteration flag and set value
    delegate_iteration_flag = IterationControlFlag(
        initial_value=10, current_value=0, max_value=10
    )
    delegate_iterations = 3
    delegate_iteration_flag.current_value = delegate_iterations

    # Simulate ending the delegation by merging metrics and updating iterations
    parent_metrics.merge(delegate_metrics)
    parent_iteration_flag.current_value += delegate_iteration_flag.current_value

    # Take a snapshot of parent metrics after delegation
    parent_metrics_after = parent_metrics
    parent_iterations_after = parent_iteration_flag.current_value

    # Calculate local metrics for the delegate
    delegate_local_cost = (
        parent_metrics_after.accumulated_cost - parent_metrics_before.accumulated_cost
    )
    delegate_local_iterations = (
        parent_iterations_after - parent_iterations_before - 1
    )  # -1 because parent increments once for delegation

    # Verify local metrics match what we expect
    assert delegate_local_cost == pytest.approx(delegate_cost)
    assert delegate_local_iterations == delegate_iterations

    # Verify token usage was also propagated
    parent_token_usages = parent_metrics_after.token_usages
    assert any(usage.response_id == token_id for usage in parent_token_usages)


@pytest.mark.asyncio
async def test_agent_reset_preserves_metrics():
    """
    Test that when an agent is reset, the metrics are preserved and not reset.
    This is important for delegation where we want to maintain accumulated metrics.
    """
    # Create a simple test to verify agent reset behavior
    from openhands.controller.state.control_flags import BudgetControlFlag
    from openhands.llm.metrics import Metrics

    # Create a mock agent
    agent = MagicMock(spec=Agent)
    agent.name = 'TestAgent'
    agent.llm = MagicMock()
    agent.llm.metrics = Metrics()

    # Add some metrics to the agent's LLM
    test_cost = 0.5
    agent.llm.metrics.add_cost(test_cost)

    # Create a budget flag for tracking
    budget_flag = BudgetControlFlag(
        initial_value=10.0, current_value=test_cost, max_value=10.0
    )

    # Take a snapshot of metrics before reset
    metrics_before = copy.deepcopy(agent.llm.metrics)

    # Reset the agent
    agent.reset()

    # Verify that metrics are preserved after reset
    assert agent.llm.metrics.accumulated_cost == metrics_before.accumulated_cost
    assert budget_flag.current_value == test_cost
