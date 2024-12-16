from unittest.mock import MagicMock

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events import EventStream
from openhands.llm.llm import LLM
from openhands.storage import InMemoryFileStore


@pytest.fixture
def agent_controller():
    llm = LLM(config=LLMConfig())
    agent = MagicMock()
    agent.name = 'test_agent'
    agent.llm = llm
    agent.config = AgentConfig()
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore())
    controller = AgentController(
        agent=agent,
        event_stream=event_stream,
        max_iterations=100,
        max_budget_per_task=10.0,
        sid='test',
        headless_mode=False,
    )
    return controller


@pytest.mark.asyncio
async def test_traffic_control_iteration_message(agent_controller):
    """Test that iteration messages are formatted as integers."""
    # Mock _react_to_exception to capture the error
    error = None

    async def mock_react_to_exception(e):
        nonlocal error
        error = e

    agent_controller._react_to_exception = mock_react_to_exception

    await agent_controller._handle_traffic_control('iteration', 200.0, 100.0)
    assert error is not None
    assert 'Current iteration: 200, max iteration: 100' in str(error)


@pytest.mark.asyncio
async def test_traffic_control_budget_message(agent_controller):
    """Test that budget messages keep decimal points."""
    # Mock _react_to_exception to capture the error
    error = None

    async def mock_react_to_exception(e):
        nonlocal error
        error = e

    agent_controller._react_to_exception = mock_react_to_exception

    await agent_controller._handle_traffic_control('budget', 15.75, 10.0)
    assert error is not None
    assert 'Current budget: 15.75, max budget: 10.00' in str(error)


@pytest.mark.asyncio
async def test_traffic_control_headless_mode(agent_controller):
    """Test that headless mode messages are formatted correctly."""
    # Mock _react_to_exception to capture the error
    error = None

    async def mock_react_to_exception(e):
        nonlocal error
        error = e

    agent_controller._react_to_exception = mock_react_to_exception

    agent_controller.headless_mode = True
    await agent_controller._handle_traffic_control('iteration', 200.0, 100.0)
    assert error is not None
    assert 'in headless mode' in str(error)
    assert 'Current iteration: 200, max iteration: 100' in str(error)
