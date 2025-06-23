import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the module, not the functions directly to avoid circular imports
import openhands.mcp.utils
from openhands.core.config.mcp_config import MCPSSEServerConfig
from openhands.events.action.mcp import MCPAction
from openhands.events.observation.mcp import MCPObservation


@pytest.mark.asyncio
async def test_create_mcp_clients_empty():
    """Test creating MCP clients with empty server list."""
    clients = await openhands.mcp.utils.create_mcp_clients([], [])
    assert clients == []


@pytest.mark.asyncio
@patch('openhands.mcp.utils.MCPClient')
async def test_create_mcp_clients_success(mock_mcp_client):
    """Test successful creation of MCP clients."""
    # Setup mock
    mock_client_instance = AsyncMock()
    mock_mcp_client.return_value = mock_client_instance
    mock_client_instance.connect_http = AsyncMock()

    # Test with two servers
    server_configs = [
        MCPSSEServerConfig(url='http://server1:8080'),
        MCPSSEServerConfig(url='http://server2:8080', api_key='test-key'),
    ]

    clients = await openhands.mcp.utils.create_mcp_clients(server_configs, [])

    # Verify
    assert len(clients) == 2
    assert mock_mcp_client.call_count == 2

    # Check that connect_http was called with correct parameters
    mock_client_instance.connect_http.assert_any_call(
        server_configs[0], conversation_id=None
    )
    mock_client_instance.connect_http.assert_any_call(
        server_configs[1], conversation_id=None
    )


@pytest.mark.asyncio
@patch('openhands.mcp.utils.MCPClient')
async def test_create_mcp_clients_connection_failure(mock_mcp_client):
    """Test handling of connection failures when creating MCP clients."""
    # Setup mock
    mock_client_instance = AsyncMock()
    mock_mcp_client.return_value = mock_client_instance

    # First connection succeeds, second fails
    mock_client_instance.connect_http.side_effect = [
        None,  # Success
        Exception('Connection failed'),  # Failure
    ]

    server_configs = [
        MCPSSEServerConfig(url='http://server1:8080'),
        MCPSSEServerConfig(url='http://server2:8080'),
    ]

    clients = await openhands.mcp.utils.create_mcp_clients(server_configs, [])

    # Verify only one client was successfully created
    assert len(clients) == 1


def test_convert_mcp_clients_to_tools_empty():
    """Test converting empty MCP clients list to tools."""
    tools = openhands.mcp.utils.convert_mcp_clients_to_tools(None)
    assert tools == []

    tools = openhands.mcp.utils.convert_mcp_clients_to_tools([])
    assert tools == []


def test_convert_mcp_clients_to_tools():
    """Test converting MCP clients to tools."""
    # Create mock clients with tools
    mock_client1 = MagicMock()
    mock_client2 = MagicMock()

    # Create mock tools
    mock_tool1 = MagicMock()
    mock_tool1.to_param.return_value = {'function': {'name': 'tool1'}}

    mock_tool2 = MagicMock()
    mock_tool2.to_param.return_value = {'function': {'name': 'tool2'}}

    mock_tool3 = MagicMock()
    mock_tool3.to_param.return_value = {'function': {'name': 'tool3'}}

    # Set up the clients with their tools
    mock_client1.tools = [mock_tool1, mock_tool2]
    mock_client2.tools = [mock_tool3]

    # Convert to tools
    tools = openhands.mcp.utils.convert_mcp_clients_to_tools(
        [mock_client1, mock_client2]
    )

    # Verify
    assert len(tools) == 3
    assert tools[0] == {'function': {'name': 'tool1'}}
    assert tools[1] == {'function': {'name': 'tool2'}}
    assert tools[2] == {'function': {'name': 'tool3'}}


@pytest.mark.asyncio
async def test_call_tool_mcp_no_clients():
    """Test calling MCP tool with no clients."""
    action = MCPAction(name='test_tool', arguments={'arg1': 'value1'})

    with pytest.raises(ValueError, match='No MCP clients found'):
        await openhands.mcp.utils.call_tool_mcp([], action)


@pytest.mark.asyncio
async def test_call_tool_mcp_no_matching_client():
    """Test calling MCP tool with no matching client."""
    # Create mock client without the requested tool
    mock_client = MagicMock()
    mock_client.tools = [MagicMock(name='other_tool')]

    action = MCPAction(name='test_tool', arguments={'arg1': 'value1'})

    with pytest.raises(ValueError, match='No matching MCP agent found for tool name'):
        await openhands.mcp.utils.call_tool_mcp([mock_client], action)


@pytest.mark.asyncio
async def test_call_tool_mcp_success():
    """Test successful MCP tool call."""
    # Create mock client with the requested tool
    mock_client = MagicMock()
    mock_tool = MagicMock()
    # Set the name attribute properly for the tool
    mock_tool.name = 'test_tool'
    mock_client.tools = [mock_tool]

    # Setup response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {'result': 'success'}

    # Setup call_tool method
    mock_client.call_tool = AsyncMock(return_value=mock_response)

    action = MCPAction(name='test_tool', arguments={'arg1': 'value1'})

    # Call the function
    observation = await openhands.mcp.utils.call_tool_mcp([mock_client], action)

    # Verify
    assert isinstance(observation, MCPObservation)
    assert json.loads(observation.content) == {'result': 'success'}
    mock_client.call_tool.assert_called_once_with('test_tool', {'arg1': 'value1'})
