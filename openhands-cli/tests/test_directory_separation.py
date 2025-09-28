"""Tests to demonstrate the fix for WORK_DIR and PERSISTENCE_DIR separation."""

import os
from unittest.mock import patch, MagicMock
from openhands.sdk import Agent, LLM, ToolSpec
from openhands_cli.locations import WORK_DIR, PERSISTENCE_DIR
from openhands_cli.tui.settings.store import AgentStore
from openhands.tools.preset.default import get_default_tools


class TestDirectorySeparation:
    """Test that WORK_DIR and PERSISTENCE_DIR are properly separated."""

    def test_work_dir_and_persistence_dir_are_different(self):
        """Test that WORK_DIR and PERSISTENCE_DIR are separate directories."""
        # WORK_DIR should be the current working directory
        assert WORK_DIR == os.getcwd()

        # PERSISTENCE_DIR should be ~/.openhands
        expected_config_dir = os.path.expanduser("~/.openhands")
        assert PERSISTENCE_DIR == expected_config_dir

        # They should be different
        assert WORK_DIR != PERSISTENCE_DIR

    def test_agent_store_uses_persistence_dir(self):
        """Test that AgentStore uses PERSISTENCE_DIR for file storage."""
        agent_store = AgentStore()
        assert agent_store.file_store.root == PERSISTENCE_DIR


class TestToolSpecFix:
    """Test that tool specs are replaced with default tools using current directory."""

    def test_tools_replaced_with_default_tools_on_load(self):
        """Test that entire tools list is replaced with default tools when loading agent."""
        # Create a mock agent with different tools and working directories
        original_working_dir = "/some/other/path"
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key", service_id="test-service"),
            tools=[
                ToolSpec(name="BashTool", params={"working_dir": original_working_dir}),
                ToolSpec(name="FileEditorTool", params={"workspace_root": original_working_dir}),
                ToolSpec(name="TaskTrackerTool", params={"save_dir": "value"}),
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

            # Verify that tools are replaced with default tools
            assert len(loaded_agent.tools) == 3  # BashTool, FileEditorTool, TaskTrackerTool

            tool_names = [tool.name for tool in loaded_agent.tools]
            assert "BashTool" in tool_names
            assert "FileEditorTool" in tool_names
            assert "TaskTrackerTool" in tool_names

            for tool_spec in loaded_agent.tools:
                if tool_spec.name == "BashTool":
                    assert tool_spec.params["working_dir"] == WORK_DIR
                    assert tool_spec.params["working_dir"] != original_working_dir
                elif tool_spec.name == "FileEditorTool":
                    assert tool_spec.params["workspace_root"] == WORK_DIR
                    assert tool_spec.params["workspace_root"] != original_working_dir
                elif tool_spec.name == "TaskTrackerTool":
                    # TaskTrackerTool should use WORK_DIR/.openhands_tasks
                    assert tool_spec.params["save_dir"] == PERSISTENCE_DIR
