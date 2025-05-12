import asyncio
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
from openhands.llm.metrics import Metrics
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
    parent_state = State(max_iterations=10)
    parent_controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
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
    async def mock_parent_step(state):
        action = AgentDelegateAction(
            agent='ChildAgent',
            inputs={'test': True},
            prompt='Please handle this task',
            thought='Delegating to child agent',
        )
        action._source = EventSource.AGENT
        action._metadata = {
            'function_name': 'delegate',
            'tool_call_id': '1',
            'model_response': 'Delegating to child agent',
            'total_calls_in_response': 1,
        }
        return action

    mock_parent_agent.step = mock_parent_step

    # Simulate a user message event to cause parent.step() to run
    message_action = MessageAction(content='please delegate now')
    message_action._source = EventSource.USER
    await parent_controller._on_event(message_action)

    # Give time for the async step() to execute
    await asyncio.sleep(1)

    # Verify that a RecallObservation was added to the event stream
    events = list(mock_event_stream.get_events())

    # Print events for debugging
    print('\nEvents in stream:')
    for i, event in enumerate(events):
        print(f'{i+1}. {type(event).__name__}')

    # Verify that all required events are present in the first 5 events
    first_five_events = events[:5]
    event_types = [type(event).__name__ for event in first_five_events]

    # Check that all required events are present
    assert (
        'SystemMessageAction' in event_types
    ), 'SystemMessageAction should be in first 5 events'
    assert 'RecallAction' in event_types, 'RecallAction should be in first 5 events'
    assert (
        'AgentStateChangedObservation' in event_types
    ), 'AgentStateChangedObservation should be in first 5 events'
    assert (
        'RecallObservation' in event_types
    ), 'RecallObservation should be in first 5 events'
    assert (
        'AgentDelegateAction' in event_types
    ), 'AgentDelegateAction should be in first 5 events'

    # Verify specific event ordering requirements
    system_msg_idx = event_types.index('SystemMessageAction')
    recall_action_idx = event_types.index('RecallAction')
    delegate_action_idx = event_types.index('AgentDelegateAction')

    # SystemMessageAction should come first
    assert system_msg_idx == 0, 'SystemMessageAction should be the first event'
    # RecallAction should come before RecallObservation
    assert recall_action_idx < event_types.index(
        'RecallObservation'
    ), 'RecallAction should come before RecallObservation'
    # AgentDelegateAction should be last
    assert delegate_action_idx == 4, 'AgentDelegateAction should be the last event'

    # Verify that a delegate agent controller is created
    assert (
        parent_controller.delegate is not None
    ), "Parent's delegate controller was not set."

    # The parent's iteration should have incremented
    assert (
        parent_controller.state.iteration == 1
    ), 'Parent iteration should be incremented after step.'

    # Now simulate that the child increments local iteration and finishes its subtask
    delegate_controller = parent_controller.delegate
    delegate_controller.state.iteration = 5  # child had some steps
    delegate_controller.state.outputs = {'delegate_result': 'done'}

    # Setup the child agent's step to return a finish action
    async def mock_child_step(state):
        action = AgentFinishAction(
            outputs={'delegate_result': 'done'},
            thought='Finished delegated task',
            task_completed=True,
            final_thought='Task completed successfully',
        )
        action._source = EventSource.AGENT
        action._metadata = {
            'function_name': 'finish',
            'tool_call_id': '1',
            'model_response': 'Task completed successfully',
            'total_calls_in_response': 1,
        }
        return action

    mock_child_agent.step = mock_child_step

    # The child is done, so we simulate it finishing by having it return an AgentFinishAction
    # This will be handled by the parent controller's on_event method
    finish_action = AgentFinishAction(
        outputs={'delegate_result': 'done'},
        thought='Finished delegated task',
        task_completed=True,
        final_thought='Task completed successfully',
    )
    finish_action._source = EventSource.AGENT
    finish_action._metadata = {
        'function_name': 'finish',
        'tool_call_id': '1',
        'model_response': 'Task completed successfully',
        'total_calls_in_response': 1,
    }
    await delegate_controller._on_event(finish_action)
    await asyncio.sleep(0.5)

    # Now the parent's delegate is None
    assert (
        parent_controller.delegate is None
    ), 'Parent delegate should be None after child finishes.'

    # Parent's global iteration is updated from the child
    assert (
        parent_controller.state.iteration == 6
    ), "Parent iteration should be the child's iteration + 1 after child is done."

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
    controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    mock_delegate = AsyncMock()
    controller.delegate = mock_delegate

    mock_delegate.state.iteration = 5
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
        assert controller.state.iteration == 0
        mock_delegate.close.assert_not_called()
    else:
        assert controller.delegate is None
        assert controller.state.iteration == 5
        mock_delegate.close.assert_called_once()

    await controller.close()
