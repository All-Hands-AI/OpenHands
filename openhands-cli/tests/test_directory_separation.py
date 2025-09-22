"""Tests to demonstrate the fix for WORK_DIR and PERSISTENCE_DIR separation."""

import os
from unittest.mock import patch, MagicMock
from openhands.sdk import Agent, LLM, ToolSpec
from openhands_cli.locations import WORK_DIR, PERSISTENCE_DIR
from openhands_cli.tui.settings.store import AgentStore


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
    """Test that bash and file editor tool specs are fixed to use current directory."""

    def test_bash_and_file_editor_tool_spec_updated_on_load(self):
        """Test that BashTool working_dir and FileEditorTool workspace_root are updated to current directory when loading agent."""
        # Create a mock agent with BashTool and FileEditorTool that have different working directories
        original_working_dir = "/some/other/path"
        mock_agent = Agent(
            llm=LLM(model="test/model", api_key="test-key"),
            tools=[
                ToolSpec(name="BashTool", params={"working_dir": original_working_dir}),
                ToolSpec(name="FileEditorTool", params={"workspace_root": original_working_dir}),
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

            for tool_spec in loaded_agent.tools:
                if tool_spec.name == "BashTool":
                    assert tool_spec.params["working_dir"] == WORK_DIR
                    assert tool_spec.params["working_dir"] != original_working_dir
                elif tool_spec.name == "FileEditorTool":
                    assert tool_spec.params["workspace_root"] == WORK_DIR
                    assert tool_spec.params["workspace_root"] != original_working_dir
                elif tool_spec.name == "TaskTrackerTool":
                    # TaskTrackerTool params should be unchanged
                    assert tool_spec.params["save_dir"] == "/some/path"


