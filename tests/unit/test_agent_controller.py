import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from litellm import ContentPolicyViolationError, ContextWindowExceededError

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State, TrafficControlState
from openhands.core.config import AppConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.core.main import run_controller
from openhands.core.schema import AgentState
from openhands.events import Event, EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import ChangeAgentStateAction, CmdRunAction, MessageAction
from openhands.events.action.agent import CondensationAction, RecallAction
from openhands.events.event import RecallType
from openhands.events.observation import (
    AgentStateChangedObservation,
    ErrorObservation,
)
from openhands.events.observation.agent import RecallObservation
from openhands.events.observation.commands import CmdOutputObservation
from openhands.events.observation.empty import NullObservation
from openhands.events.serialization import event_to_dict
from openhands.llm import LLM
from openhands.llm.metrics import Metrics, TokenUsage
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def temp_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_event_stream'))


@pytest.fixture(scope='function')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = AppConfig().get_llm_config()
    return agent


@pytest.fixture
def mock_event_stream():
    mock = MagicMock(
        spec=EventStream,
        event_stream=EventStream(sid='test', file_store=InMemoryFileStore({})),
    )
    mock.get_latest_event_id.return_value = 0
    return mock


@pytest.fixture
def test_event_stream():
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore({}))
    return event_stream


@pytest.fixture
def mock_runtime() -> Runtime:
    runtime = MagicMock(
        spec=Runtime,
        event_stream=test_event_stream,
    )
    return runtime


@pytest.fixture
def mock_memory() -> Memory:
    memory = MagicMock(
        spec=Memory,
        event_stream=test_event_stream,
    )
    return memory


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


async def send_event_to_controller(controller, event):
    await controller._on_event(event)
    await asyncio.sleep(0.1)
    controller._pending_action = None


@pytest.mark.asyncio
async def test_set_agent_state(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    await controller.set_agent_state_to(AgentState.RUNNING)
    assert controller.get_agent_state() == AgentState.RUNNING

    await controller.set_agent_state_to(AgentState.PAUSED)
    assert controller.get_agent_state() == AgentState.PAUSED
    await controller.close()


@pytest.mark.asyncio
async def test_on_event_message_action(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.state.agent_state = AgentState.RUNNING
    message_action = MessageAction(content='Test message')
    await send_event_to_controller(controller, message_action)
    assert controller.get_agent_state() == AgentState.RUNNING
    await controller.close()


@pytest.mark.asyncio
async def test_on_event_change_agent_state_action(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.state.agent_state = AgentState.RUNNING
    change_state_action = ChangeAgentStateAction(agent_state=AgentState.PAUSED)
    await send_event_to_controller(controller, change_state_action)
    assert controller.get_agent_state() == AgentState.PAUSED
    await controller.close()


@pytest.mark.asyncio
async def test_react_to_exception(mock_agent, mock_event_stream, mock_status_callback):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        status_callback=mock_status_callback,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    error_message = 'Test error'
    await controller._react_to_exception(RuntimeError(error_message))
    controller.status_callback.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_react_to_content_policy_violation(
    mock_agent, mock_event_stream, mock_status_callback
):
    """Test that the controller properly handles content policy violations from the LLM."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        status_callback=mock_status_callback,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    controller.state.agent_state = AgentState.RUNNING

    # Create and handle the content policy violation error
    error = ContentPolicyViolationError(
        message='Output blocked by content filtering policy',
        model='gpt-4',
        llm_provider='openai',
    )
    await controller._react_to_exception(error)

    # Verify the status callback was called with correct parameters
    mock_status_callback.assert_called_once_with(
        'error',
        'STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION',
        'STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION',
    )

    # Verify the state was updated correctly
    assert controller.state.last_error == 'STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION'
    assert controller.state.agent_state == AgentState.ERROR

    await controller.close()


@pytest.mark.asyncio
async def test_run_controller_with_fatal_error(test_event_stream, mock_memory):
    config = AppConfig()

    agent = MagicMock(spec=Agent)
    agent = MagicMock(spec=Agent)

    def agent_step_fn(state):
        print(f'agent_step_fn received state: {state}')
        return CmdRunAction(command='ls')

    agent.step = agent_step_fn
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = config.get_llm_config()

    runtime = MagicMock(spec=Runtime)

    def on_event(event: Event):
        if isinstance(event, CmdRunAction):
            error_obs = ErrorObservation('You messed around with Jim')
            error_obs._cause = event.id
            test_event_stream.add_event(error_obs, EventSource.USER)

    test_event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = test_event_stream

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
        memory=mock_memory,
    )
    print(f'state: {state}')
    events = list(test_event_stream.get_events())
    print(f'event_stream: {events}')
    error_observations = test_event_stream.get_matching_events(
        reverse=True, limit=1, event_types=(AgentStateChangedObservation)
    )
    assert len(error_observations) == 1
    error_observation = error_observations[0]
    assert state.iteration == 3
    assert state.agent_state == AgentState.ERROR
    assert state.last_error == 'AgentStuckInLoopError: Agent got stuck in a loop'
    assert (
        error_observation.reason == 'AgentStuckInLoopError: Agent got stuck in a loop'
    )
    assert len(events) == 11


@pytest.mark.asyncio
async def test_run_controller_stop_with_stuck(test_event_stream, mock_memory):
    config = AppConfig()
    agent = MagicMock(spec=Agent)

    def agent_step_fn(state):
        print(f'agent_step_fn received state: {state}')
        return CmdRunAction(command='ls')

    agent.step = agent_step_fn
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = config.get_llm_config()
    runtime = MagicMock(spec=Runtime)

    def on_event(event: Event):
        if isinstance(event, CmdRunAction):
            non_fatal_error_obs = ErrorObservation(
                'Non fatal error here to trigger loop'
            )
            non_fatal_error_obs._cause = event.id
            test_event_stream.add_event(non_fatal_error_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = test_event_stream

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
        memory=mock_memory,
    )
    events = list(test_event_stream.get_events())
    print(f'state: {state}')
    for i, event in enumerate(events):
        print(f'event {i}: {event_to_dict(event)}')

    assert state.iteration == 3
    assert len(events) == 11
    # check the eventstream have 4 pairs of repeated actions and observations
    repeating_actions_and_observations = events[4:12]
    for action, observation in zip(
        repeating_actions_and_observations[0::2],
        repeating_actions_and_observations[1::2],
    ):
        action_dict = event_to_dict(action)
        observation_dict = event_to_dict(observation)
        assert action_dict['action'] == 'run' and action_dict['args']['command'] == 'ls'
        assert (
            observation_dict['observation'] == 'error'
            and observation_dict['content'] == 'Non fatal error here to trigger loop'
        )
    last_event = event_to_dict(events[-1])
    assert last_event['extras']['agent_state'] == 'error'
    assert last_event['observation'] == 'agent_state_changed'

    assert state.agent_state == AgentState.ERROR
    assert state.last_error == 'AgentStuckInLoopError: Agent got stuck in a loop'


@pytest.mark.asyncio
async def test_max_iterations_extension(mock_agent, mock_event_stream):
    # Test with headless_mode=False - should extend max_iterations
    initial_state = State(max_iterations=10)

    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
        initial_state=initial_state,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.iteration = 10
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL

    # Trigger throttling by calling _step() when we hit max_iterations
    await controller._step()
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    assert controller.state.agent_state == AgentState.ERROR

    # Simulate a new user message
    message_action = MessageAction(content='Test message')
    message_action._source = EventSource.USER
    await send_event_to_controller(controller, message_action)

    # Max iterations should be extended to current iteration + initial max_iterations
    assert (
        controller.state.max_iterations == 20
    )  # Current iteration (10 initial because _step() should not have been executed) + initial max_iterations (10)
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    assert controller.state.agent_state == AgentState.RUNNING

    # Close the controller to clean up
    await controller.close()

    # Test with headless_mode=True - should NOT extend max_iterations
    initial_state = State(max_iterations=10)
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=initial_state,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.iteration = 10
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL

    # Simulate a new user message
    message_action = MessageAction(content='Test message')
    message_action._source = EventSource.USER
    await send_event_to_controller(controller, message_action)

    # Max iterations should NOT be extended in headless mode
    assert controller.state.max_iterations == 10  # Original value unchanged

    # Trigger throttling by calling _step() when we hit max_iterations
    await controller._step()

    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    assert controller.state.agent_state == AgentState.ERROR
    await controller.close()


@pytest.mark.asyncio
async def test_step_max_budget(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        max_budget_per_task=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.metrics.accumulated_cost = 10.1
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    await controller._step()
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    assert controller.state.agent_state == AgentState.ERROR
    await controller.close()


@pytest.mark.asyncio
async def test_step_max_budget_headless(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        max_budget_per_task=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.metrics.accumulated_cost = 10.1
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    await controller._step()
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    # In headless mode, throttling results in an error
    assert controller.state.agent_state == AgentState.ERROR
    await controller.close()


@pytest.mark.asyncio
async def test_reset_with_pending_action_no_observation(mock_agent, mock_event_stream):
    """Test reset() when there's a pending action with tool call metadata but no observation."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a pending action with tool call metadata
    pending_action = CmdRunAction(command='test')
    pending_action.tool_call_metadata = {
        'function': 'test_function',
        'args': {'arg1': 'value1'},
    }
    controller._pending_action = pending_action

    # Call reset
    controller._reset()

    # Verify that an ErrorObservation was added to the event stream
    mock_event_stream.add_event.assert_called_once()
    args, kwargs = mock_event_stream.add_event.call_args
    error_obs, source = args
    assert isinstance(error_obs, ErrorObservation)
    assert error_obs.content == 'The action has not been executed.'
    assert error_obs.tool_call_metadata == pending_action.tool_call_metadata
    assert error_obs._cause == pending_action.id
    assert source == EventSource.AGENT

    # Verify that pending action was reset
    assert controller._pending_action is None

    # Verify that agent.reset() was called
    mock_agent.reset.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_reset_with_pending_action_existing_observation(
    mock_agent, mock_event_stream
):
    """Test reset() when there's a pending action with tool call metadata and an existing observation."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a pending action with tool call metadata
    pending_action = CmdRunAction(command='test')
    pending_action.tool_call_metadata = {
        'function': 'test_function',
        'args': {'arg1': 'value1'},
    }
    controller._pending_action = pending_action

    # Add an existing observation to the history
    existing_obs = ErrorObservation(content='Previous error')
    existing_obs.tool_call_metadata = pending_action.tool_call_metadata
    controller.state.history.append(existing_obs)

    # Call reset
    controller._reset()

    # Verify that no new ErrorObservation was added to the event stream
    mock_event_stream.add_event.assert_not_called()

    # Verify that pending action was reset
    assert controller._pending_action is None

    # Verify that agent.reset() was called
    mock_agent.reset.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_reset_without_pending_action(mock_agent, mock_event_stream):
    """Test reset() when there's no pending action."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Call reset
    controller._reset()

    # Verify that no ErrorObservation was added to the event stream
    mock_event_stream.add_event.assert_not_called()

    # Verify that pending action is None
    assert controller._pending_action is None

    # Verify that agent.reset() was called
    mock_agent.reset.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_reset_with_pending_action_no_metadata(
    mock_agent, mock_event_stream, monkeypatch
):
    """Test reset() when there's a pending action without tool call metadata."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a pending action without tool call metadata
    pending_action = CmdRunAction(command='test')
    # Mock hasattr to return False for tool_call_metadata
    original_hasattr = hasattr

    def mock_hasattr(obj, name):
        if obj == pending_action and name == 'tool_call_metadata':
            return False
        return original_hasattr(obj, name)

    monkeypatch.setattr('builtins.hasattr', mock_hasattr)
    controller._pending_action = pending_action

    # Call reset
    controller._reset()

    # Verify that no ErrorObservation was added to the event stream
    mock_event_stream.add_event.assert_not_called()

    # Verify that pending action was reset
    assert controller._pending_action is None

    # Verify that agent.reset() was called
    mock_agent.reset.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_run_controller_max_iterations_has_metrics(
    test_event_stream, mock_memory
):
    config = AppConfig(
        max_iterations=3,
    )
    event_stream = test_event_stream

    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = config.get_llm_config()

    def agent_step_fn(state):
        print(f'agent_step_fn received state: {state}')
        # Mock the cost of the LLM
        agent.llm.metrics.add_cost(10.0)
        print(
            f'agent.llm.metrics.accumulated_cost: {agent.llm.metrics.accumulated_cost}'
        )
        return CmdRunAction(command='ls')

    agent.step = agent_step_fn

    runtime = MagicMock(spec=Runtime)

    def on_event(event: Event):
        if isinstance(event, CmdRunAction):
            non_fatal_error_obs = ErrorObservation(
                'Non fatal error. event id: ' + str(event.id)
            )
            non_fatal_error_obs._cause = event.id
            event_stream.add_event(non_fatal_error_obs, EventSource.ENVIRONMENT)

    event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = event_stream

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    event_stream.subscribe(EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4()))

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
        memory=mock_memory,
    )
    assert state.iteration == 3
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
        == 'RuntimeError: Agent reached maximum iteration in headless mode. Current iteration: 3, max iteration: 3'
    )
    error_observations = test_event_stream.get_matching_events(
        reverse=True, limit=1, event_types=(AgentStateChangedObservation)
    )
    assert len(error_observations) == 1
    error_observation = error_observations[0]

    assert (
        error_observation.reason
        == 'RuntimeError: Agent reached maximum iteration in headless mode. Current iteration: 3, max iteration: 3'
    )

    assert (
        state.metrics.accumulated_cost == 10.0 * 3
    ), f'Expected accumulated cost to be 30.0, but got {state.metrics.accumulated_cost}'


@pytest.mark.asyncio
async def test_notify_on_llm_retry(mock_agent, mock_event_stream, mock_status_callback):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        status_callback=mock_status_callback,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller._notify_on_llm_retry(1, 2)
    controller.status_callback.assert_called_once_with('info', 'STATUS$LLM_RETRY', ANY)
    await controller.close()


@pytest.mark.asyncio
async def test_context_window_exceeded_error_handling(
    mock_agent, mock_runtime, test_event_stream
):
    """Test that context window exceeded errors are handled correctly by the controller, providing a smaller view but keeping the history intact."""
    max_iterations = 5
    error_after = 2

    class StepState:
        def __init__(self):
            self.has_errored = False
            self.index = 0
            self.views = []

        def step(self, state: State):
            self.views.append(state.view)

            # Wait until the right step to throw the error, and make sure we
            # only throw it once.
            if self.index < error_after or self.has_errored:
                self.index += 1
                return MessageAction(content=f'Test message {self.index}')

            error = ContextWindowExceededError(
                message='prompt is too long: 233885 tokens > 200000 maximum',
                model='',
                llm_provider='',
            )
            self.has_errored = True
            raise error

    step_state = StepState()
    mock_agent.step = step_state.step
    mock_agent.config = AgentConfig()

    # Because we're sending message actions, we need to respond to the recall
    # actions that get generated as a response.

    # We do that by playing the role of the recall module -- subscribe to the
    # event stream and respond to recall actions by inserting fake recall
    # obesrvations.
    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )
    mock_runtime.event_stream = test_event_stream

    # Now we can run the controller for a fixed number of steps. Since the step
    # state is set to error out before then, if this terminates and we have a
    # record of the error being thrown we can be confident that the controller
    # handles the truncation correctly.
    final_state = await asyncio.wait_for(
        run_controller(
            config=AppConfig(max_iterations=max_iterations),
            initial_user_action=MessageAction(content='INITIAL'),
            runtime=mock_runtime,
            sid='test',
            agent=mock_agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=mock_memory,
        ),
        timeout=10,
    )

    # Check that the context window exception was thrown and the controller
    # called the agent's `step` function the right number of times.
    assert step_state.has_errored
    assert len(step_state.views) == max_iterations
    print('step_state.views: ', step_state.views)

    # Look at pre/post-step views. Normally, these should always increase in
    # size (because we return a message action, which triggers a recall, which
    # triggers a recall response). But if the pre/post-views are on the turn
    # when we throw the context window exceeded error, we should see the
    # post-step view compressed.
    for index, (first_view, second_view) in enumerate(
        zip(step_state.views[:-1], step_state.views[1:])
    ):
        if index == error_after:
            assert len(first_view) > len(second_view)
        else:
            assert len(first_view) < len(second_view)

    # The final state's history should contain:
    # - max_iterations number of message actions,
    # - 1 recall actions,
    # - 1 recall observations,
    # - 1 condensation action.
    assert (
        len(
            [event for event in final_state.history if isinstance(event, MessageAction)]
        )
        == max_iterations
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, MessageAction)
                and event.source == EventSource.AGENT
            ]
        )
        == max_iterations - 1
    )
    assert (
        len([event for event in final_state.history if isinstance(event, RecallAction)])
        == 1
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, RecallObservation)
            ]
        )
        == 1
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, CondensationAction)
            ]
        )
        == 1
    )
    assert (
        len(final_state.history) == max_iterations + 3
    )  # 1 condensation action, 1 recall action, 1 recall observation

    assert len(final_state.view) == len(step_state.views[-1]) + 1

    # And these two representations of the state are _not_ the same.
    assert len(final_state.history) != len(final_state.view)


@pytest.mark.asyncio
async def test_run_controller_with_context_window_exceeded_with_truncation(
    mock_agent, mock_runtime, mock_memory, test_event_stream
):
    """Tests that the controller can make progress after handling context window exceeded errors, as long as enable_history_truncation is ON"""

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # If the state has more than one message and we haven't errored yet,
            # throw the context window exceeded error
            if len(state.history) > 3 and not self.has_errored:
                error = ContextWindowExceededError(
                    message='prompt is too long: 233885 tokens > 200000 maximum',
                    model='',
                    llm_provider='',
                )
                self.has_errored = True
                raise error

            return MessageAction(content=f'STEP {len(state.history)}')

    step_state = StepState()
    mock_agent.step = step_state.step
    mock_agent.config = AgentConfig()

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )
    mock_runtime.event_stream = test_event_stream

    try:
        state = await asyncio.wait_for(
            run_controller(
                config=AppConfig(max_iterations=5),
                initial_user_action=MessageAction(content='INITIAL'),
                runtime=mock_runtime,
                sid='test',
                agent=mock_agent,
                fake_user_response_fn=lambda _: 'repeat',
                memory=mock_memory,
            ),
            timeout=10,
        )

    # A timeout error indicates the run_controller entrypoint is not making
    # progress
    except asyncio.TimeoutError as e:
        raise AssertionError(
            'The run_controller function did not complete in time.'
        ) from e

    # Hitting the iteration limit indicates the controller is failing for the
    # expected reason
    assert state.iteration == 5
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
        == 'RuntimeError: Agent reached maximum iteration in headless mode. Current iteration: 5, max iteration: 5'
    )

    # Check that the context window exceeded error was raised during the run
    assert step_state.has_errored


@pytest.mark.asyncio
async def test_run_controller_with_context_window_exceeded_without_truncation(
    mock_agent, mock_runtime, mock_memory, test_event_stream
):
    """Tests that the controller would quit upon context window exceeded errors without enable_history_truncation ON."""

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # If the state has more than one message and we haven't errored yet,
            # throw the context window exceeded error
            if len(state.history) > 3 and not self.has_errored:
                error = ContextWindowExceededError(
                    message='prompt is too long: 233885 tokens > 200000 maximum',
                    model='',
                    llm_provider='',
                )
                self.has_errored = True
                raise error

            return MessageAction(content=f'STEP {len(state.history)}')

    step_state = StepState()
    mock_agent.step = step_state.step
    mock_agent.config = AgentConfig()
    mock_agent.config.enable_history_truncation = False

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )
    mock_runtime.event_stream = test_event_stream
    try:
        state = await asyncio.wait_for(
            run_controller(
                config=AppConfig(max_iterations=3),
                initial_user_action=MessageAction(content='INITIAL'),
                runtime=mock_runtime,
                sid='test',
                agent=mock_agent,
                fake_user_response_fn=lambda _: 'repeat',
                memory=mock_memory,
            ),
            timeout=10,
        )

    # A timeout error indicates the run_controller entrypoint is not making
    # progress
    except asyncio.TimeoutError as e:
        raise AssertionError(
            'The run_controller function did not complete in time.'
        ) from e

    # Hitting the iteration limit indicates the controller is failing for the
    # expected reason
    assert state.iteration == 2
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
        == 'LLMContextWindowExceedError: Conversation history longer than LLM context window limit. Consider turning on enable_history_truncation config to avoid this error'
    )

    error_observations = test_event_stream.get_matching_events(
        reverse=True, limit=1, event_types=(AgentStateChangedObservation)
    )
    assert len(error_observations) == 1
    error_observation = error_observations[0]
    assert (
        error_observation.reason
        == 'LLMContextWindowExceedError: Conversation history longer than LLM context window limit. Consider turning on enable_history_truncation config to avoid this error'
    )

    # Check that the context window exceeded error was raised during the run
    assert step_state.has_errored


@pytest.mark.asyncio
async def test_run_controller_with_memory_error(test_event_stream):
    config = AppConfig()
    event_stream = test_event_stream

    # Create a propert agent that returns an action without an ID
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = config.get_llm_config()

    # Create a real action to return from the mocked step function
    def agent_step_fn(state):
        return MessageAction(content='Agent returned a message')

    agent.step = agent_step_fn

    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream

    # Create a real Memory instance
    memory = Memory(event_stream=event_stream, sid='test-memory')

    # Patch the _find_microagent_knowledge method to raise our test exception
    def mock_find_microagent_knowledge(*args, **kwargs):
        raise RuntimeError('Test memory error')

    with patch.object(
        memory, '_find_microagent_knowledge', side_effect=mock_find_microagent_knowledge
    ):
        state = await run_controller(
            config=config,
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            agent=agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=memory,
        )

    assert state.iteration == 0
    assert state.agent_state == AgentState.ERROR
    assert state.last_error == 'Error: RuntimeError'


@pytest.mark.asyncio
async def test_action_metrics_copy():
    # Setup
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)

    # Create agent with metrics
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    metrics = Metrics(model_name='test-model')
    metrics.accumulated_cost = 0.05

    # Add multiple token usages - we should get the last one in the action
    usage1 = TokenUsage(
        model='test-model',
        prompt_tokens=5,
        completion_tokens=10,
        cache_read_tokens=2,
        cache_write_tokens=2,
        response_id='test-id-1',
    )

    usage2 = TokenUsage(
        model='test-model',
        prompt_tokens=10,
        completion_tokens=20,
        cache_read_tokens=5,
        cache_write_tokens=5,
        response_id='test-id-2',
    )

    metrics.token_usages = [usage1, usage2]

    # Set the accumulated token usage
    metrics._accumulated_token_usage = TokenUsage(
        model='test-model',
        prompt_tokens=15,  # 5 + 10
        completion_tokens=30,  # 10 + 20
        cache_read_tokens=7,  # 2 + 5
        cache_write_tokens=7,  # 2 + 5
        response_id='accumulated',
    )

    # Add a cost instance - should not be included in action metrics
    # This will increase accumulated_cost by 0.02
    metrics.add_cost(0.02)

    # Add a response latency - should not be included in action metrics
    metrics.add_response_latency(0.5, 'test-id-2')

    agent.llm.metrics = metrics

    # Mock agent step to return an action
    action = MessageAction(content='Test message')

    def agent_step_fn(state):
        return action

    agent.step = agent_step_fn

    # Create controller with correct parameters
    controller = AgentController(
        agent=agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Execute one step
    controller.state.agent_state = AgentState.RUNNING
    await controller._step()

    # Get the last event from event stream
    events = list(event_stream.get_events())
    assert len(events) > 0
    last_action = events[-1]

    # Verify metrics were copied correctly
    assert last_action.llm_metrics is not None
    assert (
        last_action.llm_metrics.accumulated_cost == 0.07
    )  # 0.05 initial + 0.02 from add_cost

    # Should not include individual token usages anymore (after the fix)
    assert len(last_action.llm_metrics.token_usages) == 0

    # But should include the accumulated token usage
    assert last_action.llm_metrics.accumulated_token_usage.prompt_tokens == 15  # 5 + 10
    assert (
        last_action.llm_metrics.accumulated_token_usage.completion_tokens == 30
    )  # 10 + 20
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_read_tokens == 7
    )  # 2 + 5
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_write_tokens == 7
    )  # 2 + 5

    # Should not include the cost history
    assert len(last_action.llm_metrics.costs) == 0

    # Should not include the response latency history
    assert len(last_action.llm_metrics.response_latencies) == 0

    # Verify that there's no latency information in the action's metrics
    # Either directly or as a calculated property
    assert not hasattr(last_action.llm_metrics, 'latency')
    assert not hasattr(last_action.llm_metrics, 'total_latency')
    assert not hasattr(last_action.llm_metrics, 'average_latency')

    # Verify it's a deep copy by modifying the original
    agent.llm.metrics.accumulated_cost = 0.1
    assert last_action.llm_metrics.accumulated_cost == 0.07

    await controller.close()


@pytest.mark.asyncio
async def test_first_user_message_with_identical_content():
    """
    Test that _first_user_message correctly identifies the first user message
    even when multiple messages have identical content but different IDs.
    Also verifies that the result is properly cached.

    The issue we're checking is that the comparison (action == self._first_user_message())
    should correctly differentiate between messages with the same content but different IDs.
    """
    # Create a real event stream for this test
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore({}))

    # Create an agent controller
    mock_agent = MagicMock(spec=Agent)
    mock_agent.llm = MagicMock(spec=LLM)
    mock_agent.llm.metrics = Metrics()
    mock_agent.llm.config = AppConfig().get_llm_config()

    controller = AgentController(
        agent=mock_agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create and add the first user message
    first_message = MessageAction(content='Hello, this is a test message')
    first_message._source = EventSource.USER
    event_stream.add_event(first_message, EventSource.USER)

    # Create and add a second user message with identical content
    second_message = MessageAction(content='Hello, this is a test message')
    second_message._source = EventSource.USER
    event_stream.add_event(second_message, EventSource.USER)

    # Verify that _first_user_message returns the first message
    first_user_message = controller._first_user_message()
    assert first_user_message is not None
    assert first_user_message.id == first_message.id  # Check IDs match
    assert first_user_message.id != second_message.id  # Different IDs
    assert first_user_message == first_message == second_message  # dataclass equality

    # Test the comparison used in the actual code
    assert first_message == first_user_message  # This should be True
    assert (
        second_message.id != first_user_message.id
    )  # This should be False, but may be True if there's a bug

    # Verify caching behavior
    assert (
        controller._cached_first_user_message is not None
    )  # Cache should be populated
    assert (
        controller._cached_first_user_message is first_user_message
    )  # Cache should store the same object

    # Mock get_events to verify it's not called again
    with patch.object(event_stream, 'get_events') as mock_get_events:
        cached_message = controller._first_user_message()
        assert cached_message is first_user_message  # Should return cached object
        mock_get_events.assert_not_called()  # Should not call get_events again

    await controller.close()


async def test_agent_controller_processes_null_observation_with_cause():
    """Test that AgentController processes NullObservation events with a cause value.

    And that the agent's step method is called as a result.
    """
    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create a Memory instance - not used directly in this test but needed for setup
    Memory(event_stream=event_stream, sid='test-session')

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

        # Events in the stream:
        # Event 0: MessageAction, ID: 0, Cause: None, Source: EventSource.USER, Content: First user message
        # Event 1: RecallAction, ID: 1, Cause: None, Source: EventSource.USER, Content: N/A
        # Event 2: NullObservation, ID: 2, Cause: 1, Source: EventSource.ENVIRONMENT, Content:
        # Event 3: AgentStateChangedObservation, ID: 3, Cause: None, Source: EventSource.ENVIRONMENT, Content:

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

        # Verify the NullObservation has a cause that points to the RecallAction
        assert null_observation.cause is not None, 'NullObservation cause is None'
        assert (
            null_observation.cause == recall_action.id
        ), f'Expected cause={recall_action.id}, got cause={null_observation.cause}'

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


def test_agent_controller_should_step_with_null_observation_cause_zero():
    """Test that AgentController's should_step method returns False for NullObservation with cause = 0."""
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
    # This should not happen, but if it does, the controller shouldn't step.
    null_observation = NullObservation(content='Test observation')
    null_observation._cause = 0  # type: ignore[attr-defined]

    # Check if should_step returns False for this observation
    result = controller.should_step(null_observation)

    # It should return False since we only want to step on NullObservation with cause > 0
    assert (
        result is False
    ), 'should_step should return False for NullObservation with cause = 0'


def test_apply_conversation_window_basic(mock_event_stream, mock_agent):
    """Test that the _apply_conversation_window method correctly prunes a list of events."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_apply_conversation_window_basic',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a sequence of events with IDs
    first_msg = MessageAction(content='Hello, start task', wait_for_response=False)
    first_msg._source = EventSource.USER
    first_msg._id = 1

    # Add agent question
    agent_msg = MessageAction(
        content='What task would you like me to perform?', wait_for_response=True
    )
    agent_msg._source = EventSource.AGENT
    agent_msg._id = 2

    # Add user response
    user_response = MessageAction(
        content='Please list all files and show me current directory',
        wait_for_response=False,
    )
    user_response._source = EventSource.USER
    user_response._id = 3

    cmd1 = CmdRunAction(command='ls')
    cmd1._id = 4
    obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=4)
    obs1._id = 5
    obs1._cause = 4

    cmd2 = CmdRunAction(command='pwd')
    cmd2._id = 6
    obs2 = CmdOutputObservation(command='pwd', content='/home', command_id=6)
    obs2._id = 7
    obs2._cause = 6

    events = [first_msg, agent_msg, user_response, cmd1, obs1, cmd2, obs2]

    # Apply truncation
    truncated = controller._apply_conversation_window(events)

    # Verify truncation occured
    # Should keep first user message and roughly half of other events
    assert (
        3 <= len(truncated) < len(events)
    )  # First message + at least one action-observation pair
    assert truncated[0] == first_msg  # First message always preserved
    assert controller.state.start_id == first_msg._id

    # Verify pairs aren't split
    for i, event in enumerate(truncated[1:]):
        if isinstance(event, CmdOutputObservation):
            assert any(e._id == event._cause for e in truncated[: i + 1])


def test_history_restoration_after_truncation(mock_event_stream, mock_agent):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_truncation',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create events with IDs
    first_msg = MessageAction(content='Start task', wait_for_response=False)
    first_msg._source = EventSource.USER
    first_msg._id = 1

    events = [first_msg]
    for i in range(5):
        cmd = CmdRunAction(command=f'cmd{i}')
        cmd._id = i + 2
        obs = CmdOutputObservation(
            command=f'cmd{i}', content=f'output{i}', command_id=cmd._id
        )
        obs._cause = cmd._id
        events.extend([cmd, obs])

    # Set up initial history
    controller.state.history = events.copy()

    # Force truncation
    controller.state.history = controller._apply_conversation_window(
        controller.state.history
    )

    # Save state
    saved_start_id = controller.state.start_id
    saved_history_len = len(controller.state.history)

    # Set up mock event stream for new controller
    mock_event_stream.get_events.return_value = controller.state.history

    # Create new controller with saved state
    new_controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_truncation',
        confirmation_mode=False,
        headless_mode=True,
    )
    new_controller.state.start_id = saved_start_id
    new_controller.state.history = mock_event_stream.get_events()

    # Verify restoration
    assert len(new_controller.state.history) == saved_history_len
    assert new_controller.state.history[0] == first_msg
    assert new_controller.state.start_id == saved_start_id
