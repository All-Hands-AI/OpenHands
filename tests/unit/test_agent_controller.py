import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import TrafficControlState
from openhands.core.exceptions import LLMMalformedActionError
from openhands.core.schema import AgentState
from openhands.events import EventStream
from openhands.events.action import ChangeAgentStateAction, MessageAction


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
    return MagicMock(spec=Agent)


@pytest.fixture
def mock_event_stream():
    return MagicMock(spec=EventStream)


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
    await controller.on_event(message_action)
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
    await controller.on_event(change_state_action)
    assert controller.get_agent_state() == AgentState.PAUSED
    await controller.close()


@pytest.mark.asyncio
async def test_report_error(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    error_message = 'Test error'
    await controller.report_error(error_message)
    assert controller.state.last_error == error_message
    controller.event_stream.add_event.assert_called_once()
    await controller.close()


@pytest.mark.asyncio
async def test_step_with_exception(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.report_error = AsyncMock()
    controller.agent.step.side_effect = LLMMalformedActionError('Malformed action')
    await controller._step()

    # Verify that report_error was called with the correct error message
    controller.report_error.assert_called_once_with('Malformed action')
    await controller.close()


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
    mock_agent, mock_event_stream, delegate_state
):
    controller = AgentController(
        agent=mock_agent,
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

    await controller._delegate_step()

    mock_delegate._step.assert_called_once()

    if delegate_state == AgentState.RUNNING:
        assert controller.delegate is not None
        assert controller.state.iteration == 0
        mock_delegate.close.assert_not_called()
    else:
        assert controller.delegate is None
        assert controller.state.iteration == 5
        mock_delegate.close.assert_called_once()

    await controller.close()


@pytest.mark.asyncio
async def test_step_max_iterations(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.iteration = 10
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    await controller._step()
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    assert controller.state.agent_state == AgentState.PAUSED
    await controller.close()


@pytest.mark.asyncio
async def test_step_max_iterations_headless(mock_agent, mock_event_stream):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    controller.state.agent_state = AgentState.RUNNING
    controller.state.iteration = 10
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    await controller._step()
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    # In headless mode, throttling results in an error
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
    assert controller.state.agent_state == AgentState.PAUSED
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
