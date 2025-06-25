# Unit tests for VsCodeRuntime

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from openhands.runtime.vscode.vscode_runtime import VsCodeRuntime
from openhands.core.config import OpenHandsConfig
from openhands.events.action import CmdRunAction, FileReadAction, FileWriteAction
from openhands.events.observation import CmdOutputObservation, FileReadObservation, ErrorObservation
from openhands.events.stream import EventStream


class TestVsCodeRuntimeConstructor:
    """Test VsCodeRuntime constructor and initialization."""
    
    def test_constructor_no_dependencies(self):
        """Test that VsCodeRuntime can be constructed without sio_server/socket_connection_id."""
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        
        # Should not raise any exceptions
        runtime = VsCodeRuntime(config=config, event_stream=event_stream)
        
        assert runtime.config is not None
        assert runtime.sid == "default"
        assert runtime.plugins == []
        assert runtime.env_vars == {}
        assert runtime.sio_server is None
        assert runtime.socket_connection_id is None
        assert runtime._running_actions == {}
        assert runtime._server_url == "http://localhost:3000"
    
    def test_constructor_with_optional_params(self):
        """Test constructor with optional parameters."""
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        
        runtime = VsCodeRuntime(
            config=config,
            event_stream=event_stream,
            sid="test_sid",
            plugins=[]
        )
        
        assert runtime.config is not None
        assert runtime.event_stream is not None
        assert runtime.sid == "test_sid"


class TestVsCodeRuntimeDiscovery:
    """Test VSCode instance discovery system."""
    
    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)
    
    @pytest.mark.asyncio
    async def test_discover_vscode_instances_success(self, runtime):
        """Test successful discovery of VSCode instances."""
        mock_response_data = {
            "instances": [
                {
                    "id": "vscode-1",
                    "name": "VSCode Instance 1",
                    "port": 3001,
                    "status": "active",
                    "workspace": "/path/to/workspace1"
                },
                {
                    "id": "vscode-2", 
                    "name": "VSCode Instance 2",
                    "port": 3002,
                    "status": "active",
                    "workspace": "/path/to/workspace2"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            instances = await runtime._get_available_vscode_instances()
            
            assert len(instances) == 2
            assert instances[0]["id"] == "vscode-1"
            assert instances[1]["id"] == "vscode-2"
    
    @pytest.mark.asyncio
    async def test_discover_vscode_instances_server_error(self, runtime):
        """Test discovery when server returns error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response
            
            instances = await runtime._get_available_vscode_instances()
            
            assert instances == []
    
    @pytest.mark.asyncio
    async def test_discover_vscode_instances_connection_error(self, runtime):
        """Test discovery when connection fails."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            instances = await runtime._get_available_vscode_instances()
            
            assert instances == []
    
    @pytest.mark.asyncio
    async def test_discovery_multiple_calls(self, runtime):
        """Test that multiple discovery calls work correctly."""
        mock_response_data = {"instances": [{"id": "vscode-1", "port": 3001}]}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # First call should make HTTP request
            instances1 = await runtime._get_available_vscode_instances()
            assert mock_get.call_count == 1
            assert len(instances1) == 1
            
            # Second call should make another HTTP request (no caching)
            instances2 = await runtime._get_available_vscode_instances()
            assert mock_get.call_count == 2  # Additional call made
            assert instances1 == instances2


class TestVsCodeRuntimeConnection:
    """Test VSCode connection management."""
    
    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, runtime):
        """Test successful connection validation."""
        connection_id = "vscode-1"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "active"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            is_valid = await runtime._validate_vscode_connection(connection_id)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, runtime):
        """Test connection validation failure."""
        connection_id = "vscode-1"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            is_valid = await runtime._validate_vscode_connection(connection_id)
            
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_discover_and_connect_success(self, runtime):
        """Test successful connection establishment."""
        mock_instances = [
            {"id": "vscode-1", "port": 3001, "status": "active", "connection_id": "conn-1"},
            {"id": "vscode-2", "port": 3002, "status": "active", "connection_id": "conn-2"}
        ]
        
        with patch.object(runtime, '_get_available_vscode_instances', return_value=mock_instances), \
             patch('openhands.server.shared.sio') as mock_sio:
            
            runtime.sio_server = mock_sio
            result = await runtime._discover_and_connect()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_discover_and_connect_no_sio_server(self, runtime):
        """Test connection when sio_server import fails."""
        with patch('openhands.server.shared.sio', side_effect=ImportError("Module not found")):
            result = await runtime._discover_and_connect()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_discover_and_connect_no_instances(self, runtime):
        """Test connection when no instances are discovered."""
        with patch.object(runtime, '_get_available_vscode_instances', return_value=[]), \
             patch('openhands.server.shared.sio') as mock_sio:
            
            runtime.sio_server = mock_sio
            result = await runtime._discover_and_connect()
            
            assert result is False


class TestVsCodeRuntimeActions:
    """Test action execution in VsCodeRuntime."""
    
    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        runtime = VsCodeRuntime(config=config, event_stream=event_stream)
        runtime._current_connection = {"id": "vscode-1", "port": 3001}
        return runtime
    
    def test_run_action_cmd_success(self, runtime):
        """Test successful command execution."""
        action = CmdRunAction(command="echo 'hello'")
        
        # Mock the connection setup
        runtime.socket_connection_id = "test-connection"
        
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch.object(runtime, '_validate_vscode_connection', new_callable=AsyncMock, return_value=True):
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "exit_code": 0,
                "output": "hello\n"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            observation = runtime.run_action(action)
            
            assert isinstance(observation, CmdOutputObservation)
            assert observation.exit_code == 0
            assert observation.content == "hello\n"
    
    def test_run_action_file_read_success(self, runtime):
        """Test successful file read."""
        action = FileReadAction(path="/test/file.txt")
        
        # Mock the connection setup
        runtime.socket_connection_id = "test-connection"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "content": "file content here"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            observation = runtime.run_action(action)
            
            assert isinstance(observation, FileReadObservation)
            assert observation.content == "file content here"
    
    def test_run_action_connection_error(self, runtime):
        """Test action execution when connection fails."""
        action = CmdRunAction(command="echo 'hello'")
        
        # No connection setup - should trigger discovery and fail
        with patch.object(runtime, '_get_available_vscode_instances', return_value=[]):
            observation = runtime.run_action(action)
            
            assert isinstance(observation, ErrorObservation)
            assert "No VSCode instances" in observation.content
    
    def test_run_action_with_valid_connection(self, runtime):
        """Test action execution with a valid connection."""
        action = CmdRunAction(command="echo 'hello'")
        
        # Set up a valid connection
        runtime.socket_connection_id = "test-connection"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "exit_code": 0,
                "output": "hello\n"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            observation = runtime.run_action(action)
            
            assert isinstance(observation, CmdOutputObservation)
            assert observation.exit_code == 0
            assert observation.content == "hello\n"


class TestVsCodeRuntimeErrorHandling:
    """Test error handling and recovery in VsCodeRuntime."""
    
    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)
    
    @pytest.mark.asyncio
    async def test_comprehensive_error_messages(self, runtime):
        """Test that error messages are comprehensive and helpful."""
        action = CmdRunAction(command="test")
        
        with patch.object(runtime, '_ensure_connection') as mock_ensure:
            mock_ensure.side_effect = RuntimeError("No VSCode instances discovered. Please ensure VSCode is running with the OpenHands extension.")
            
            observation = await runtime.run_action(action)
            
            assert isinstance(observation, ErrorObservation)
            assert "No VSCode instances discovered" in observation.content
            assert "Please ensure VSCode is running" in observation.content
    
    @pytest.mark.asyncio
    async def test_recovery_logic(self, runtime):
        """Test recovery logic when connections fail."""
        # Set up initial connection
        runtime._current_connection = {"id": "vscode-1", "port": 3001}
        
        action = CmdRunAction(command="test")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Connection lost")
            
            # Mock successful recovery
            new_connection = {"id": "vscode-2", "port": 3002}
            with patch.object(runtime, '_ensure_connection', return_value=new_connection):
                
                # This should trigger recovery
                await runtime.run_action(action)
                
                # Verify connection was updated
                assert runtime._current_connection == new_connection


class TestVsCodeRuntimeIntegration:
    """Integration tests for VsCodeRuntime components."""
    
    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)
    
    @pytest.mark.asyncio
    async def test_full_workflow_success(self, runtime):
        """Test complete workflow from discovery to action execution."""
        mock_instances = [{"id": "vscode-1", "port": 3001, "status": "active"}]
        action = CmdRunAction(command="pwd")
        
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            # Mock discovery
            mock_discovery_response = AsyncMock()
            mock_discovery_response.status = 200
            mock_discovery_response.json = AsyncMock(return_value=mock_instances)
            
            # Mock validation
            mock_validation_response = AsyncMock()
            mock_validation_response.status = 200
            mock_validation_response.json = AsyncMock(return_value={"status": "healthy"})
            
            # Mock action execution
            mock_action_response = AsyncMock()
            mock_action_response.status = 200
            mock_action_response.json = AsyncMock(return_value={
                "exit_code": 0,
                "output": "/current/directory\n"
            })
            
            mock_get.return_value.__aenter__.return_value = mock_discovery_response
            mock_post.return_value.__aenter__.return_value = mock_action_response
            
            # Execute action - should trigger full workflow
            observation = await runtime.run_action(action)
            
            assert isinstance(observation, CmdOutputObservation)
            assert observation.exit_code == 0
            assert "/current/directory" in observation.content
            assert runtime._current_connection == mock_instances[0]