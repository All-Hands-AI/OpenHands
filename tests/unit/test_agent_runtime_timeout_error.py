import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.exceptions import AgentRuntimeTimeoutError
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import CmdRunAction
from openhands.runtime.runtime_status import RuntimeStatus


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.llm = MagicMock()
    agent.llm.metrics = MagicMock()
    agent.llm.config = MagicMock()
    agent.config = MagicMock()
    agent.config.enable_mcp = True
    return agent


@pytest.fixture
def mock_event_stream():
    mock = MagicMock(spec=EventStream)
    mock.get_latest_event_id.return_value = 0
    return mock


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


@pytest.mark.asyncio
async def test_agent_runtime_timeout_error(mock_agent, mock_event_stream, mock_status_callback):
    """Test that AgentRuntimeTimeoutError is properly handled and propagated."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        status_callback=mock_status_callback,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    
    # Set up the controller state
    controller.state.agent_state = AgentState.RUNNING
    
    # Create a timeout error
    timeout_error = AgentRuntimeTimeoutError(
        'Runtime failed to return execute_action before the requested timeout of 120s'
    )
    
    # Call the exception handler with the timeout error
    await controller._react_to_exception(timeout_error)
    
    # Verify the status callback was called with the correct parameters
    mock_status_callback.assert_called_once_with(
        'error',
        RuntimeStatus.ERROR_RUNTIME_TIMEOUT,
        'AgentRuntimeTimeoutError: Runtime failed to return execute_action before the requested timeout of 120s',
    )
    
    # Verify the state was updated correctly
    assert controller.state.last_error == 'AgentRuntimeTimeoutError: Runtime failed to return execute_action before the requested timeout of 120s'
    assert controller.state.agent_state == AgentState.ERROR
    
    await controller.close()


@pytest.mark.asyncio
async def test_runtime_timeout_error_propagation(mock_agent, mock_event_stream):
    """Test that AgentRuntimeTimeoutError is properly propagated to the state's last_error."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )
    
    # Set up the controller state
    controller.state.agent_state = AgentState.RUNNING
    
    # Create a timeout error
    timeout_error = AgentRuntimeTimeoutError(
        'Runtime failed to return execute_action before the requested timeout of 120s'
    )
    
    # Call the exception handler with the timeout error
    await controller._react_to_exception(timeout_error)
    
    # Verify the error is properly stored in the state
    assert 'AgentRuntimeTimeoutError' in controller.state.last_error
    assert 'Runtime failed to return execute_action before the requested timeout of 120s' in controller.state.last_error
    
    await controller.close()