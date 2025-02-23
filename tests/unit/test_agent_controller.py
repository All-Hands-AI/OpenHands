import asyncio
import logging
from unittest.mock import ANY, AsyncMock, MagicMock
from uuid import uuid4

import pytest
from litellm import ContextWindowExceededError

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State, TrafficControlState
from openhands.core.config import AppConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.core.main import run_controller
from openhands.core.schema import AgentState
from openhands.events import Event, EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import ChangeAgentStateAction, CmdRunAction, MessageAction
from openhands.events.observation import (
    ErrorObservation,
)
from openhands.events.serialization import event_to_dict
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
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
    mock = MagicMock(spec=EventStream)
    mock.get_latest_event_id.return_value = 0
    return mock


@pytest.fixture
def mock_runtime() -> Runtime:
    return MagicMock(
        spec=Runtime,
        event_stream=EventStream(sid='test', file_store=InMemoryFileStore({})),
    )


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


async def send_event_to_controller(controller, event):
    await controller._on_event(event)
    await asyncio.sleep(0.1)


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
async def test_run_controller_with_fatal_error():
    config = AppConfig()
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)

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
            event_stream.add_event(error_obs, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = event_stream

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
    )
    print(f'state: {state}')
    events = list(event_stream.get_events())
    print(f'event_stream: {events}')
    assert state.iteration == 4
    assert state.agent_state == AgentState.ERROR
    assert state.last_error == 'AgentStuckInLoopError: Agent got stuck in a loop'
    assert len(events) == 11


@pytest.mark.asyncio
async def test_run_controller_stop_with_stuck():
    config = AppConfig()
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)

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
            event_stream.add_event(non_fatal_error_obs, EventSource.ENVIRONMENT)

    event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = event_stream

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
    )
    events = list(event_stream.get_events())
    print(f'state: {state}')
    for i, event in enumerate(events):
        print(f'event {i}: {event_to_dict(event)}')

    assert state.iteration == 4
    assert len(events) == 11
    # check the eventstream have 4 pairs of repeated actions and observations
    repeating_actions_and_observations = events[2:10]
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
async def test_subscriber_behavior(temp_dir):
    """Test the behavior of subscribers, especially around unsubscribe and resubscribe scenarios."""
    # Create a real event stream with a file store
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)
    
    # Create a list to track callback invocations
    callback_invocations = []
    
    # Create multiple callbacks
    def callback1(event):
        callback_invocations.append(('callback1', event))
    
    def callback2(event):
        callback_invocations.append(('callback2', event))
    
    # Add multiple subscribers
    callback1_id = str(uuid4())
    callback2_id = str(uuid4())
    
    # Subscribe both callbacks
    event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback1, callback1_id)
    event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback2, callback2_id)
    
    # Add a test event
    test_event = MessageAction(content='Test message')
    event_stream.add_event(test_event, EventSource.USER)
    
    # Give time for event processing
    await asyncio.sleep(0.1)
    
    # Both callbacks should have received the event
    assert len(callback_invocations) == 2
    assert ('callback1', test_event) in callback_invocations
    assert ('callback2', test_event) in callback_invocations
    
    # Clear invocations
    callback_invocations.clear()
    
    # Unsubscribe one callback
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback1_id)
    
    # Add another test event
    test_event2 = MessageAction(content='Test message 2')
    event_stream.add_event(test_event2, EventSource.USER)
    
    # Give time for event processing
    await asyncio.sleep(0.1)
    
    # Only callback2 should have received the event
    assert len(callback_invocations) == 1
    assert ('callback2', test_event2) in callback_invocations
    
    # Try to unsubscribe again - should log warning but not error
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback1_id)
    
    # Resubscribe callback1
    event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback1, callback1_id)
    
    # Clear invocations
    callback_invocations.clear()
    
    # Add another test event
    test_event3 = MessageAction(content='Test message 3')
    event_stream.add_event(test_event3, EventSource.USER)
    
    # Give time for event processing
    await asyncio.sleep(0.1)
    
    # Both callbacks should receive the event again
    assert len(callback_invocations) == 2
    assert ('callback1', test_event3) in callback_invocations
    assert ('callback2', test_event3) in callback_invocations
    
    # Unsubscribe a non-existent callback - should log warning
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, str(uuid4()))
    
    # Unsubscribe from a non-existent subscriber - should log warning
    event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER, callback1_id)
    
    # Clean up
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback1_id)
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback2_id)
    event_stream.close()


@pytest.mark.asyncio
async def test_subscriber_stress(temp_dir):
    """Stress test subscriber behavior to try to replicate the bug where subscriber warning appears
    even though the callback still exists and is being invoked."""
    # Create a real event stream with a file store
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)
    
    # Create a list to track callback invocations
    callback_invocations = []
    
    # Create a callback that simulates some processing time
    async def async_callback(event):
        await asyncio.sleep(0.01)  # Simulate some async work
        callback_invocations.append(('async_callback', event))
    
    def callback(event):
        asyncio.run(async_callback(event))
    
    # Create multiple subscriber IDs
    subscriber_ids = [str(uuid4()) for _ in range(5)]
    active_callbacks = {sid: [] for sid in subscriber_ids}  # Track active callback IDs for each subscriber
    
    try:
        # Subscribe and unsubscribe in rapid succession
        for i in range(10):  # Do 10 rounds of subscribe/unsubscribe
            for sid in subscriber_ids:
                # Generate a new callback ID for each subscription
                callback_id = str(uuid4())
                active_callbacks[sid].append(callback_id)
                
                # Subscribe with new callback ID
                event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback, callback_id)
                
                # Add a test event
                test_event = MessageAction(content=f'Test message {i}-{sid}')
                event_stream.add_event(test_event, EventSource.USER)
                
                # Give minimal time for event processing
                await asyncio.sleep(0.001)
                
                # Unsubscribe the previous callback if it exists
                if len(active_callbacks[sid]) > 1:
                    old_callback_id = active_callbacks[sid].pop(0)
                    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, old_callback_id)
                
                # Add another test event
                test_event2 = MessageAction(content=f'Test message {i}-{sid}-2')
                event_stream.add_event(test_event2, EventSource.USER)
                
                # Occasionally try to unsubscribe a non-existent callback
                if i % 3 == 0:
                    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, str(uuid4()))
        
        # Give time for all events to be processed
        await asyncio.sleep(1)
        
        # Verify that we received events
        # We should have 2 events per iteration per subscriber
        expected_events = 10 * len(subscriber_ids) * 2
        assert len(callback_invocations) >= expected_events * 0.9, f"Expected at least 90% of {expected_events} events, got {len(callback_invocations)}"
        
    finally:
        # Clean up all callbacks
        for sid in subscriber_ids:
            for callback_id in active_callbacks[sid]:
                event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback_id)
        event_stream.close()


@pytest.mark.asyncio
async def test_subscriber_unsubscribe_bug(temp_dir):
    """Test the specific case where a callback continues to be invoked even after
    getting 'Subscriber not found during unsubscribe' warning."""
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)
    
    callback_invocations = []
    
    # Create a callback that takes some time to complete
    async def async_callback(event):
        await asyncio.sleep(0.05)  # Long enough to ensure we can test during execution
        callback_invocations.append(('async_callback', event))
    
    def callback(event):
        asyncio.run(async_callback(event))
    
    callback_id = str(uuid4())
    
    # Subscribe the callback
    event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback, callback_id)
    
    # Add an event to start the callback processing
    test_event1 = MessageAction(content='Test message 1')
    event_stream.add_event(test_event1, EventSource.USER)
    
    # Give a tiny bit of time for the event to be queued but not processed
    await asyncio.sleep(0.01)
    
    # Try to unsubscribe while the callback is still processing
    event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, callback_id)
    
    # Add another event - this should not trigger the callback if unsubscribe worked
    test_event2 = MessageAction(content='Test message 2')
    event_stream.add_event(test_event2, EventSource.USER)
    
    # Wait for all processing to complete
    await asyncio.sleep(0.2)
    
    # Clean up
    event_stream.close()
    
    # Check the invocations
    print(f"Callback invocations: {callback_invocations}")
    assert len(callback_invocations) == 1, (
        f"Expected only 1 invocation (from first event), but got {len(callback_invocations)}. "
        f"This indicates the callback was still being called after unsubscribe."
    )
    assert callback_invocations[0][1] == test_event1, (
        "Expected only the first event to be processed"
    )


@pytest.mark.asyncio
async def test_subscriber_unsubscribe_concurrent(temp_dir):
    """Test concurrent subscribe/unsubscribe operations to try to trigger the bug
    where callbacks remain active after unsubscribe."""
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)
    
    callback_invocations = []
    unsubscribe_warnings = []
    
    # Create a callback that takes some time to complete
    async def async_callback(event):
        await asyncio.sleep(0.05)  # Long enough to create overlap
        callback_invocations.append(('async_callback', event))
    
    def callback(event):
        asyncio.run(async_callback(event))
    
    # Create a custom logger to capture warnings
    class WarningCaptureHandler(logging.Handler):
        def emit(self, record):
            if "Subscriber not found during unsubscribe" in record.getMessage():
                unsubscribe_warnings.append(record.getMessage())
    
    logger = logging.getLogger('openhands.events.stream')
    handler = WarningCaptureHandler()
    logger.addHandler(handler)
    
    try:
        # Create multiple subscribers and callbacks
        subscriber_ids = [EventStreamSubscriber.RUNTIME, EventStreamSubscriber.AGENT_CONTROLLER]
        callback_ids = {sid: [] for sid in subscriber_ids}
        
        for i in range(5):  # 5 rounds of subscribe/unsubscribe
            for subscriber_id in subscriber_ids:
                # Subscribe with a new callback ID
                callback_id = str(uuid4())
                callback_ids[subscriber_id].append(callback_id)
                event_stream.subscribe(subscriber_id, callback, callback_id)
                
                # Add an event
                test_event = MessageAction(content=f'Test message {i}-{subscriber_id}')
                event_stream.add_event(test_event, EventSource.USER)
                
                # Small delay to allow some overlap
                await asyncio.sleep(0.01)
                
                # Try to unsubscribe the previous callback if it exists
                if len(callback_ids[subscriber_id]) > 1:
                    old_id = callback_ids[subscriber_id][-2]
                    event_stream.unsubscribe(subscriber_id, old_id)
                
                # Add another event
                test_event2 = MessageAction(content=f'Test message {i}-{subscriber_id}-2')
                event_stream.add_event(test_event2, EventSource.USER)
        
        # Wait for all processing to complete
        await asyncio.sleep(0.5)
        
        # Check for any cases where we got a warning but the callback was still invoked
        print(f"Unsubscribe warnings: {unsubscribe_warnings}")
        print(f"Callback invocations: {len(callback_invocations)}")
        
        # If we got any "Subscriber not found" warnings, we should check that those
        # callbacks were not invoked after the warning
        if unsubscribe_warnings:
            # The number of invocations should be less than the total number of events
            total_events = len(subscriber_ids) * 5 * 2  # subscribers * rounds * events per round
            assert len(callback_invocations) < total_events, (
                f"Got {len(callback_invocations)} invocations for {total_events} events "
                f"even though some callbacks were unsubscribed"
            )
    
    finally:
        # Clean up
        for subscriber_id in subscriber_ids:
            for callback_id in callback_ids[subscriber_id]:
                event_stream.unsubscribe(subscriber_id, callback_id)
        event_stream.close()
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_subscriber_race_condition(temp_dir):
    """Test specifically for race conditions in subscriber management."""
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)
    
    callback_invocations = []
    
    # Create a callback that takes some time to complete
    async def slow_callback(event):
        await asyncio.sleep(0.05)  # Long enough to create potential race conditions
        callback_invocations.append(('slow_callback', event))
    
    def callback(event):
        asyncio.run(slow_callback(event))
    
    # Create tasks to subscribe/unsubscribe concurrently
    async def subscribe_unsubscribe(sid: str):
        for _ in range(5):
            event_stream.subscribe(EventStreamSubscriber.RUNTIME, callback, sid)
            test_event = MessageAction(content=f'Test message for {sid}')
            event_stream.add_event(test_event, EventSource.USER)
            await asyncio.sleep(0.01)  # Small delay to increase chance of race condition
            event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, sid)
            await asyncio.sleep(0.01)
    
    # Run multiple subscribe/unsubscribe operations concurrently
    subscriber_ids = [str(uuid4()) for _ in range(3)]
    tasks = [subscribe_unsubscribe(sid) for sid in subscriber_ids]
    await asyncio.gather(*tasks)
    
    # Give time for all events to be processed
    await asyncio.sleep(1)
    
    # Clean up
    for sid in subscriber_ids:
        event_stream.unsubscribe(EventStreamSubscriber.RUNTIME, sid)
    event_stream.close()


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
async def test_run_controller_max_iterations_has_metrics():
    config = AppConfig(
        max_iterations=3,
    )
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)

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

    state = await run_controller(
        config=config,
        initial_user_action=MessageAction(content='Test message'),
        runtime=runtime,
        sid='test',
        agent=agent,
        fake_user_response_fn=lambda _: 'repeat',
    )
    assert state.iteration == 3
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
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
async def test_context_window_exceeded_error_handling(mock_agent, mock_event_stream):
    """Test that context window exceeded errors are handled correctly by truncating history."""

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # Append a few messages to the history -- these will be truncated when we throw the error
            state.history = [
                MessageAction(content='Test message 0'),
                MessageAction(content='Test message 1'),
            ]

            error = ContextWindowExceededError(
                message='prompt is too long: 233885 tokens > 200000 maximum',
                model='',
                llm_provider='',
            )
            self.has_errored = True
            raise error

    state = StepState()
    mock_agent.step = state.step
    mock_agent.config = AgentConfig()

    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Set the agent running and take a step in the controller -- this is similar
    # to taking a single step using `run_controller`, but much easier to control
    # termination for testing purposes
    controller.state.agent_state = AgentState.RUNNING
    await controller._step()

    # Check that the error was thrown and the history has been truncated
    assert state.has_errored
    assert controller.state.history == [MessageAction(content='Test message 1')]


@pytest.mark.asyncio
async def test_run_controller_with_context_window_exceeded_with_truncation(
    mock_agent, mock_runtime
):
    """Tests that the controller can make progress after handling context window exceeded errors, as long as enable_history_truncation is ON"""

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # If the state has more than one message and we haven't errored yet,
            # throw the context window exceeded error
            if len(state.history) > 1 and not self.has_errored:
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

    try:
        state = await asyncio.wait_for(
            run_controller(
                config=AppConfig(max_iterations=3),
                initial_user_action=MessageAction(content='INITIAL'),
                runtime=mock_runtime,
                sid='test',
                agent=mock_agent,
                fake_user_response_fn=lambda _: 'repeat',
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
    assert state.iteration == 3
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
        == 'RuntimeError: Agent reached maximum iteration in headless mode. Current iteration: 3, max iteration: 3'
    )

    # Check that the context window exceeded error was raised during the run
    assert step_state.has_errored


@pytest.mark.asyncio
async def test_run_controller_with_context_window_exceeded_without_truncation(
    mock_agent, mock_runtime
):
    """Tests that the controller would quit upon context window exceeded errors without enable_history_truncation ON."""

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # If the state has more than one message and we haven't errored yet,
            # throw the context window exceeded error
            if len(state.history) > 1 and not self.has_errored:
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

    try:
        state = await asyncio.wait_for(
            run_controller(
                config=AppConfig(max_iterations=3),
                initial_user_action=MessageAction(content='INITIAL'),
                runtime=mock_runtime,
                sid='test',
                agent=mock_agent,
                fake_user_response_fn=lambda _: 'repeat',
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

    # Check that the context window exceeded error was raised during the run
    assert step_state.has_errored
