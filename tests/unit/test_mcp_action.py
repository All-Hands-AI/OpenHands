from unittest import mock

import pytest
from mcp.types import CallToolResult, TextContent

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import McpAction
from openhands.events.observation import Observation
from openhands.events.serialization import event_to_dict
from openhands.mcp.client import MCPClientTool
from openhands.runtime.action_execution_server import ActionExecutor, ActionRequest


@pytest.mark.asyncio
async def test_mcp_action_execution():
    # Mock the init_user_and_working_directory function to avoid requiring root privileges
    with mock.patch(
        'openhands.runtime.action_execution_server.init_user_and_working_directory',
        return_value=None,
    ):
        # Create a mock ActionExecutor with MCP configuration
        executor = ActionExecutor(
            plugins_to_load=[],
            work_dir='/tmp',
            username='test_user',
            user_id=1000,
            browsergym_eval_env=None,
        )

        # Set up MCP configuration
        executor.sse_mcp_servers = ['http://localhost:8000']

        # Create a McpAction instance with arguments
        action = McpAction(name='test_action', arguments='{}')

        # Create a mock tool
        mock_tool = MCPClientTool(
            name='test_action', description='Test tool', inputSchema={}
        )

        # Mock the MCP client and its call_tool method
        mock_client = mock.AsyncMock()
        mock_client.call_tool.return_value = CallToolResult(
            content=[TextContent(text='MCP action received', type='text')]
        )
        mock_client.tools = [mock_tool]  # Add the tool to the client

        # Mock the connect_sse method to succeed
        mock_client.connect_sse = mock.AsyncMock()

        # Mock create_mcp_clients to return our mock client
        with mock.patch(
            'openhands.runtime.action_execution_server.create_mcp_clients',
            return_value=[mock_client],
        ):
            # Execute the action
            action_request = ActionRequest(
                action=event_to_dict(action),
            )
            executor.process_request(action_request)
            observation = await executor.call_tool_mcp(action)
            logger.warning(f'Observation: {observation}')

            # Verify the observation
            assert isinstance(observation, Observation)
            assert 'MCP action received' in observation.content

            # Verify the mock was called correctly
            mock_client.call_tool.assert_called_once_with(action.name, {})
