"""Tests to demonstrate the fix for WORK_DIR and CONFIGURATIONS_DIR separation."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from openhands.sdk import Agent, LLM, ToolSpec
from openhands_cli.locations import WORK_DIR, CONFIGURATIONS_DIR
from openhands_cli.tui.settings.store import AgentStore


class TestDirectorySeparation:
    """Test that WORK_DIR and CONFIGURATIONS_DIR are properly separated."""

    def test_work_dir_and_configurations_dir_are_different(self):
        """Test that WORK_DIR and CONFIGURATIONS_DIR are separate directories."""
        # WORK_DIR should be the current working directory
        assert WORK_DIR == os.getcwd()
        
        # CONFIGURATIONS_DIR should be ~/.openhands
        expected_config_dir = os.path.expanduser("~/.openhands")
        assert CONFIGURATIONS_DIR == expected_config_dir
        
        # They should be different
        assert WORK_DIR != CONFIGURATIONS_DIR

    def test_agent_store_uses_configurations_dir(self):
        """Test that AgentStore uses CONFIGURATIONS_DIR for file storage."""
        agent_store = AgentStore()
        assert agent_store.file_store.root == CONFIGURATIONS_DIR

    @patch('openhands_cli.tui.settings.store.LocalFileStore')
    def test_agent_store_initialization(self, mock_file_store):
        """Test that AgentStore initializes with correct directory."""
        AgentStore()
        mock_file_store.assert_called_once_with(root=CONFIGURATIONS_DIR)


class TestBashToolSpecFix:
    """Test that bash tool spec is fixed to use current directory."""

    def test_bash_tool_spec_updated_on_load(self):
        """Test that BashTool working_dir is updated to current directory when loading agent."""
        # Create a mock agent with BashTool that has a different working_dir
        original_working_dir = "/some/other/path"
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[
                ToolSpec(name="BashTool", params={"working_dir": original_working_dir}),
                ToolSpec(name="FileEditorTool"),
            ]
        )
        
        # Mock the file store to return our test agent
        with patch('openhands_cli.tui.settings.store.LocalFileStore') as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()
            
            agent_store = AgentStore()
            loaded_agent = agent_store.load()
            
            # Verify the agent was loaded
            assert loaded_agent is not None
            
            # Find the BashTool spec
            bash_tool_spec = None
            for tool_spec in loaded_agent.tools:
                if tool_spec.name == "BashTool":
                    bash_tool_spec = tool_spec
                    break
            
            # Verify BashTool was found and working_dir was updated
            assert bash_tool_spec is not None
            assert bash_tool_spec.params["working_dir"] == WORK_DIR
            assert bash_tool_spec.params["working_dir"] != original_working_dir

    def test_non_bash_tools_unchanged_on_load(self):
        """Test that non-BashTool specs are not modified when loading agent."""
        # Create a mock agent with various tools
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[
                ToolSpec(name="BashTool", params={"working_dir": "/old/path"}),
                ToolSpec(name="FileEditorTool"),
                ToolSpec(name="TaskTrackerTool", params={"save_dir": "/some/path"}),
            ]
        )
        
        # Mock the file store to return our test agent
        with patch('openhands_cli.tui.settings.store.LocalFileStore') as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()
            
            agent_store = AgentStore()
            loaded_agent = agent_store.load()
            
            # Verify the agent was loaded
            assert loaded_agent is not None
            
            # Check that non-BashTool specs are unchanged
            for tool_spec in loaded_agent.tools:
                if tool_spec.name == "FileEditorTool":
                    # FileEditorTool should have no params or unchanged params
                    assert tool_spec.params is None or tool_spec.params == {}
                elif tool_spec.name == "TaskTrackerTool":
                    # TaskTrackerTool params should be unchanged
                    assert tool_spec.params["save_dir"] == "/some/path"

    def test_agent_without_tools_loads_correctly(self):
        """Test that agents without tools load correctly."""
        # Create a mock agent without tools
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[]
        )
        
        # Mock the file store to return our test agent
        with patch('openhands_cli.tui.settings.store.LocalFileStore') as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()
            
            agent_store = AgentStore()
            loaded_agent = agent_store.load()
            
            # Verify the agent was loaded correctly
            assert loaded_agent is not None
            assert loaded_agent.tools == []

    def test_agent_with_empty_tools_loads_correctly(self):
        """Test that agents with empty tools list load correctly."""
        # Create a mock agent with empty tools list
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[]
        )
        
        # Mock the file store to return our test agent
        with patch('openhands_cli.tui.settings.store.LocalFileStore') as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()
            
            agent_store = AgentStore()
            loaded_agent = agent_store.load()
            
            # Verify the agent was loaded correctly
            assert loaded_agent is not None
            assert loaded_agent.tools == []

    def test_bash_tool_without_params_gets_working_dir(self):
        """Test that BashTool without params gets working_dir added."""
        # Create a mock agent with BashTool that has no params
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[
                ToolSpec(name="BashTool"),  # No params
            ]
        )
        
        # Mock the file store to return our test agent
        with patch('openhands_cli.tui.settings.store.LocalFileStore') as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()
            
            agent_store = AgentStore()
            loaded_agent = agent_store.load()
            
            # Verify the agent was loaded
            assert loaded_agent is not None
            
            # Find the BashTool spec
            bash_tool_spec = None
            for tool_spec in loaded_agent.tools:
                if tool_spec.name == "BashTool":
                    bash_tool_spec = tool_spec
                    break
            
            # Verify BashTool was found and working_dir was added
            assert bash_tool_spec is not None
            assert bash_tool_spec.params is not None
            assert bash_tool_spec.params["working_dir"] == WORK_DIR


class TestIntegration:
    """Integration tests to verify the fixes work together."""

    def test_agent_creation_uses_work_dir_for_tools(self):
        """Test that when creating new agents, tools use WORK_DIR appropriately."""
        from openhands.sdk.preset.default import get_default_agent
        
        # Create a default agent with WORK_DIR
        llm = LLM(model="test/model", api_key="test-key")
        agent = get_default_agent(llm=llm, working_dir=WORK_DIR, cli_mode=True)
        
        # Verify that BashTool uses WORK_DIR
        bash_tool_spec = None
        for tool_spec in agent.tools:
            if tool_spec.name == "BashTool":
                bash_tool_spec = tool_spec
                break
        
        assert bash_tool_spec is not None
        assert bash_tool_spec.params["working_dir"] == WORK_DIR

    def test_configurations_stored_separately_from_work_dir(self):
        """Test that configurations are stored in CONFIGURATIONS_DIR, not WORK_DIR."""
        # This test verifies that the configuration storage is separate from work directory
        
        # Create a temporary directory to simulate a different working directory
        with tempfile.TemporaryDirectory() as temp_work_dir:
            # Change to the temporary directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_work_dir)
                
                # Import locations after changing directory to get updated WORK_DIR
                import importlib
                import openhands_cli.locations
                importlib.reload(openhands_cli.locations)
                from openhands_cli.locations import WORK_DIR as NEW_WORK_DIR, CONFIGURATIONS_DIR as NEW_CONFIGURATIONS_DIR
                
                # Verify WORK_DIR changed but CONFIGURATIONS_DIR stayed the same
                assert NEW_WORK_DIR == temp_work_dir
                assert NEW_CONFIGURATIONS_DIR == os.path.expanduser("~/.openhands")
                assert NEW_WORK_DIR != NEW_CONFIGURATIONS_DIR
                
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
                # Reload locations to restore original values
                importlib.reload(openhands_cli.locations)