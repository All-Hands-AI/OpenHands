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
    CreatePlanAction,
    MarkTaskAction,
    MessageAction,
)
from openhands.events.action.agent import RecallAction
from openhands.events.event import Event, RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.stream import EventStreamSubscriber
from openhands.events.tool import ToolCallMetadata
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
    agent.mcp_tools = []

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

    # create plan action
    create_plan_action = CreatePlanAction(
        plan_id='plan_1',
        title='Test Plan',
        tasks=['Task 1', 'Task 2'],
    )
    create_plan_action._source = EventSource.AGENT
    create_plan_action.tool_call_metadata = ToolCallMetadata(
        tool_call_id='tool_call_1',
        function_name='create_plan',
        total_calls_in_response=1,
        model_response={
            'id': 'chatcmpl-123abc456def',
            'object': 'chat.completion',
            'created': 1699896916,
            'model': 'gpt-4-1106-preview',
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': None,
                        'tool_calls': [
                            {
                                'id': 'call_abc123xyz789',
                                'type': 'function',
                                'function': {
                                    'name': 'create_plan',
                                    'arguments': '{"plan_id": "plan_1", "title": "Test Plan", "tasks": ["Task 1", "Task 2"]}',
                                },
                            }
                        ],
                    },
                    'finish_reason': 'tool_calls',
                }
            ],
            'usage': {
                'prompt_tokens': 82,
                'completion_tokens': 39,
                'total_tokens': 121,
            },
        },
    )

    mock_parent_agent.step.return_value = create_plan_action

    # Simulate a user message event to cause parent.step() to run
    message_action = MessageAction(content='please create a plan')
    message_action._source = EventSource.USER
    await parent_controller._on_event(message_action)
    await asyncio.sleep(1)
    # Verify that a RecallObservation was added to the event stream
    events = list(mock_event_stream.get_events())
    # SystemMessageAction, RecallAction, AgentChangeState, MessageAction, CreatePlanAction, CreatePlanObservation, MarkTaskAction
    assert mock_event_stream.get_latest_event_id() == 7
    # a RecallObservation, a CreatePlanAction and a MarkTaskAction should be in the list
    assert any(isinstance(event, RecallObservation) for event in events)
    assert any(isinstance(event, CreatePlanAction) for event in events)
    assert any(isinstance(event, MarkTaskAction) for event in events)

    # Setup a delegate action from the parent
    delegate_action = AgentDelegateAction(
        agent='ChildAgent',
        inputs={'task': 'Task 1'},
    )
    delegate_action.tool_call_metadata = ToolCallMetadata(
        tool_call_id='tool_call_2',
        function_name='delegate_task',
        total_calls_in_response=1,
        model_response={
            'id': 'chatcmpl-123abc456def',
            'object': 'chat.completion',
            'created': 1699896916,
            'model': 'gpt-4-1106-preview',
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': None,
                        'tool_calls': [
                            {
                                'id': 'call_abc123xyz789',
                                'type': 'function',
                                'function': {
                                    'name': 'delegate_task',
                                    'arguments': '{"task": "Task 1"}',
                                },
                            }
                        ],
                    },
                    'finish_reason': 'tool_calls',
                }
            ],
            'usage': {
                'prompt_tokens': 82,
                'completion_tokens': 39,
                'total_tokens': 121,
            },
        },
    )
    delegate_action._source = EventSource.AGENT
    mock_parent_agent.step.return_value = delegate_action

    # Simulate a user message event to cause parent.step() to run
    message_action = MessageAction(content='please delegate now')
    message_action._source = EventSource.USER
    await parent_controller._on_event(message_action)

    # Give time for the async step() to execute
    await asyncio.sleep(1)

    # Verify that a RecallObservation was added to the event stream
    events = list(mock_event_stream.get_events())

    # a RecallObservation and an AgentDelegateAction should be in the list
    assert any(isinstance(event, RecallObservation) for event in events)
    assert any(isinstance(event, AgentDelegateAction) for event in events)

    # Verify that a delegate agent controller is created
    assert (
        parent_controller.delegate is not None
    ), "Parent's delegate controller was not set."

    # The parent's iteration should have incremented
    assert (
        parent_controller.state.iteration == 3
    ), 'Parent iteration should be incremented after step.'

    # Now simulate that the child increments local iteration and finishes its subtask
    delegate_controller = parent_controller.delegate
    delegate_controller.state.iteration = 5  # child had some steps
    delegate_controller.state.outputs = {'delegate_result': 'done'}

    # The child is done, so we simulate it finishing:
    child_finish_action = AgentFinishAction()
    await delegate_controller._on_event(child_finish_action)
    await asyncio.sleep(1)

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
