import pytest
from unittest.mock import AsyncMock, MagicMock, ANY
from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.core.config import AgentConfig

class TestAgent(Agent):
    """Concrete test agent implementation"""
    def __init__(self):
        mock_llm = MagicMock()
        mock_config = MagicMock()
        super().__init__(llm=mock_llm, config=mock_config)
        self.mcp_router = MagicMock()
        
    def step(self, state):
        return None  # Abstract method implementation

class TestMCPIntegration:
    @pytest.fixture
    def mock_client_session(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "success"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        return mock_session

    @pytest.fixture
    def mock_controller(self, mock_client_session):
        controller = MagicMock(spec=AgentController)
        controller.make_mcp_request = AsyncMock()
        controller._create_client_session = MagicMock(return_value=mock_client_session)
        return controller

    @pytest.mark.asyncio
    async def test_mcp_request(self, mock_controller, mock_client_session):
        """Test basic MCP request routing"""
        agent = TestAgent()
        agent.mcp_capabilities = ["llm", "vision"]
        
        # Setup test server config
        server_config = {
            "enabled": True,
            "host": "test-mcp-server",
            "port": 8000,
            "capabilities": ["llm", "vision"]
        }
        
        # Mock router responses
        agent.mcp_router = MagicMock()
        agent.mcp_router.select_server.return_value = server_config
        agent.mcp_router.get_server_url.return_value = "http://test-mcp-server:8000"
        
        # Monkey patch instance check
        agent.__class__ = type('MixedAgent', (Agent, AgentController), {})
        
        # Mock the agent's request method directly
        agent.make_mcp_request = AsyncMock(return_value={"status": "success"})
        
        # Execute test
        response = await agent.mcp_request("config", {"key": "value"})
        
        # Verify the mock was called correctly
        agent.make_mcp_request.assert_awaited_once_with(
            endpoint="config",
            payload={"key": "value"},
            required_capabilities=["llm", "vision"]
        )
        assert response["status"] == "success"

    def test_capability_registration(self):
        """Test dynamic capability registration"""
        agent = TestAgent()
        assert agent.mcp_capabilities == ["general"]
        
        agent.register_mcp_capability("audio")
        assert "audio" in agent.mcp_capabilities
        
        # Test no duplicates
        agent.register_mcp_capability("audio")
        assert len(agent.mcp_capabilities) == 2  # general + audio