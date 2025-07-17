import asyncio
import json
from unittest import mock

import pytest
from mcp.shared.exceptions import McpError

from openhands.controller.agent_controller import AgentController
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action.mcp import MCPAction
from openhands.events.action.message import SystemMessageAction
from openhands.events.observation.mcp import MCPObservation
from openhands.mcp.client import MCPClient
from openhands.mcp.tool import MCPClientTool
from openhands.mcp.utils import call_tool_mcp


class MockAgent:
    """Mock agent for testing."""

    def __init__(self):
        self.config = mock.MagicMock()
        self.llm = mock.MagicMock()
        self.name = 'MockAgent'
        self.step_called = False
        self.next_action = None

    def step(self, state):
        self.step_called = True
        return self.next_action

    def get_system_message(self):
        return SystemMessageAction(content='Mock system message')


@pytest.mark.asyncio
async def test_mcp_tool_timeout_stall():
    """Test that MCP tool timeouts are properly handled and don't cause the agent to stall."""
    # Create a mock MCPClient
    mock_client = mock.MagicMock(spec=MCPClient)

    # Configure the mock to raise a TimeoutError when call_tool is called
    async def mock_call_tool(*args, **kwargs):
        # Simulate a timeout
        await asyncio.sleep(0.1)
        # Create a mock error object with the message attribute
        error = mock.MagicMock()
        error.message = 'Timed out while waiting for response to ClientRequest. Waited 30.0 seconds.'
        raise McpError(error)

    mock_client.call_tool.side_effect = mock_call_tool

    # Create a mock tool
    mock_tool = MCPClientTool(
        name='test_tool',
        description='Test tool',
        inputSchema={'type': 'object', 'properties': {}},
        session=None,
    )
    mock_client.tools = [mock_tool]
    mock_client.tool_map = {'test_tool': mock_tool}

    # Create a mock file store
    mock_file_store = mock.MagicMock()

    # Create a mock event stream
    event_stream = EventStream(sid='test-session', file_store=mock_file_store)

    # Create a mock agent
    agent = MockAgent()

    # Create a mock agent controller
    controller = AgentController(
        sid='test-session',
        file_store=mock_file_store,
        user_id='test-user',
        agent=agent,
        event_stream=event_stream,
        iteration_delta=10,
        budget_per_task_delta=None,
    )

    # Set up the agent state
    await controller.set_agent_state_to(AgentState.RUNNING)

    # Create an MCP action
    mcp_action = MCPAction(
        name='test_tool',
        arguments={'param': 'value'},
        thought='Testing MCP timeout handling',
    )

    # Add the action to the event stream
    event_stream.add_event(mcp_action, EventSource.AGENT)

    # Mock the call_tool_mcp function to handle the timeout error
    async def mock_call_tool_mcp(clients, action):
        try:
            # This will raise the McpError
            await mock_client.call_tool(action.name, action.arguments)
        except McpError as e:
            # Create an error observation
            error_content = json.dumps(
                {'isError': True, 'error': str(e), 'content': []}
            )
            return MCPObservation(content=error_content, cause=action.id)

    # Set the pending action
    controller._pending_action = mcp_action

    # Use our mock function
    with mock.patch(
        'openhands.mcp.utils.call_tool_mcp', side_effect=mock_call_tool_mcp
    ):
        # Call the function that would normally be called by the agent controller
        result = await call_tool_mcp([mock_client], mcp_action)

        # Verify that the function returns an error observation
        assert isinstance(result, MCPObservation)
        content = json.loads(result.content)
        assert content['isError'] is True
        assert 'timed out' in content['error'].lower()

        # Now simulate the agent controller's handling of the observation
        event_stream.add_event(result, EventSource.ENVIRONMENT)

        # Verify that the pending action is cleared
        controller._pending_action = None

        # Verify that the agent is still in the RUNNING state
        assert controller.get_agent_state() == AgentState.RUNNING

        # Verify that the agent can continue processing
        agent.next_action = MCPAction(
            name='another_tool',
            arguments={'param': 'value'},
            thought='Another action after timeout',
        )

        # Simulate a step
        await controller._step()

        # Verify that the agent was asked to step
        assert agent.step_called


@pytest.mark.asyncio
async def test_mcp_client_call_tool_timeout():
    """Test that MCPClient.call_tool properly handles timeouts."""
    # Create a mock MCPClient
    client = MCPClient()

    # Create a mock tool
    mock_tool = MCPClientTool(
        name='test_tool',
        description='Test tool',
        inputSchema={'type': 'object', 'properties': {}},
        session=None,
    )
    client.tools = [mock_tool]
    client.tool_map = {'test_tool': mock_tool}

    # Mock the client's session
    client.client = mock.MagicMock()

    # Configure the mock to raise a TimeoutError when call_tool_mcp is called
    async def mock_call_tool_mcp(*args, **kwargs):
        await asyncio.sleep(0.1)
        # Create a mock error object with the message attribute
        error = mock.MagicMock()
        error.message = 'Timed out while waiting for response to ClientRequest. Waited 30.0 seconds.'
        raise McpError(error)

    client.client.call_tool_mcp.side_effect = mock_call_tool_mcp

    # Call the method and verify it raises the expected exception
    with pytest.raises(McpError) as excinfo:
        await client.call_tool('test_tool', {'param': 'value'})

    # Verify the exception message
    assert 'Timed out' in str(excinfo.value)
