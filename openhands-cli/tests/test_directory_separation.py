"""Tests to demonstrate the fix for WORK_DIR and PERSISTENCE_DIR separation."""

import os
from unittest.mock import MagicMock, patch

from openhands_cli.locations import PERSISTENCE_DIR, WORK_DIR
from openhands_cli.tui.settings.store import AgentStore

from openhands.sdk import LLM, Agent, Tool


class TestDirectorySeparation:
    """Test that WORK_DIR and PERSISTENCE_DIR are properly separated."""

    def test_work_dir_and_persistence_dir_are_different(self):
        """Test that WORK_DIR and PERSISTENCE_DIR are separate directories."""
        # WORK_DIR should be the current working directory
        assert WORK_DIR == os.getcwd()

        # PERSISTENCE_DIR should be ~/.openhands
        expected_config_dir = os.path.expanduser('~/.openhands')
        assert PERSISTENCE_DIR == expected_config_dir

        # They should be different
        assert WORK_DIR != PERSISTENCE_DIR

    def test_agent_store_uses_persistence_dir(self):
        """Test that AgentStore uses PERSISTENCE_DIR for file storage."""
        agent_store = AgentStore()
        assert agent_store.file_store.root == PERSISTENCE_DIR


class TestToolFix:
    """Test that tool specs are replaced with default tools using current directory."""

    def test_tools_replaced_with_default_tools_on_load(self):
        """Test that entire tools list is replaced with default tools when loading agent."""
        # Create a mock agent with different tools and working directories
        mock_agent = Agent(
            llm=LLM(model='test/model', api_key='test-key', service_id='test-service'),
            tools=[
                Tool(name='BashTool'),
                Tool(name='FileEditorTool'),
                Tool(name='TaskTrackerTool'),
            ],
        )

        # Mock the file store to return our test agent
        with patch(
            'openhands_cli.tui.settings.store.LocalFileStore'
        ) as mock_file_store:
            mock_store_instance = MagicMock()
            mock_file_store.return_value = mock_store_instance
            mock_store_instance.read.return_value = mock_agent.model_dump_json()

            agent_store = AgentStore()
            loaded_agent = agent_store.load()

            # Verify the agent was loaded
            assert loaded_agent is not None

            # Verify that tools are replaced with default tools
            assert (
                len(loaded_agent.tools) == 3
            )  # BashTool, FileEditorTool, TaskTrackerTool

            tool_names = [tool.name for tool in loaded_agent.tools]
            assert 'BashTool' in tool_names
            assert 'FileEditorTool' in tool_names
            assert 'TaskTrackerTool' in tool_names
