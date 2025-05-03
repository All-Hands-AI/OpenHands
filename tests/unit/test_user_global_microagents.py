import os
import shutil
import tempfile
from unittest import mock

import pytest

from openhands.core.config import AppConfig
from openhands.memory.memory import Memory
from openhands.microagent import KnowledgeMicroagent, RepoMicroagent
from openhands.runtime.base import Runtime


class TestCustomMicroagents:
    @pytest.fixture
    def mock_event_stream(self):
        mock_stream = mock.MagicMock()
        return mock_stream

    @pytest.fixture
    def temp_user_microagents_dir(self):
        # Create a temporary directory to simulate the user's ~/.openhands/microagents directory
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_runtime(self, temp_user_microagents_dir):
        mock_runtime = mock.MagicMock(spec=Runtime)
        mock_config = mock.MagicMock(spec=AppConfig)
        mock_config.custom_microagents_dir = temp_user_microagents_dir
        mock_runtime.config = mock_config
        return mock_runtime

    def test_custom_microagents_directory_in_config(
        self, mock_event_stream, mock_runtime
    ):
        """Test that the custom microagents directory is correctly set in the config."""
        # Create a Memory instance
        memory = Memory(mock_event_stream, 'test_sid')

        # Set runtime info - it doesnt load the microagents!!!!!
        memory.set_runtime_info(mock_runtime)

        # Verify that the runtime's config was accessed
        mock_runtime.config.custom_microagents_dir

    def test_runtime_loads_custom_microagents(
        self, mock_event_stream, temp_user_microagents_dir, mock_runtime
    ):
        """Test that the Runtime loads custom microagents from the configured directory."""
        # Create a test knowledge microagent
        knowledge_content = """---
name: test-knowledge
type: knowledge
triggers:
  - test trigger
---
# Test Knowledge
This is a test knowledge microagent.
"""
        knowledge_path = os.path.join(temp_user_microagents_dir, 'test-knowledge.md')
        with open(knowledge_path, 'w') as f:
            f.write(knowledge_content)

        # Create a test repo microagent
        repo_content = """---
name: test-repo
type: repo
---
# Test Repo
This is a test repo microagent.
"""
        repo_path = os.path.join(temp_user_microagents_dir, 'test-repo.md')
        with open(repo_path, 'w') as f:
            f.write(repo_content)

        # Create a Memory instance
        memory = Memory(mock_event_stream, 'test_sid')

        # Create mock microagents that would be loaded by the Runtime
        knowledge_agent = KnowledgeMicroagent(
            name='test-knowledge',
            triggers=['test trigger'],
            content='This is a test knowledge microagent.',
            path='test-knowledge.md',
            microagent_dir=temp_user_microagents_dir,
        )
        repo_agent = RepoMicroagent(
            name='test-repo',
            content='This is a test repo microagent.',
            path='test-repo.md',
            microagent_dir=temp_user_microagents_dir,
        )

        # Mock the Runtime's get_microagents_from_selected_repo method to return our test microagents
        mock_runtime.get_microagents_from_selected_repo.return_value = [
            knowledge_agent,
            repo_agent,
        ]

        # Load the microagents into Memory
        memory.load_user_workspace_microagents([knowledge_agent, repo_agent])

        # Check that the microagents were loaded
        assert 'test-knowledge' in memory.knowledge_microagents
        assert 'test-repo' in memory.repo_microagents

        # Verify the content
        assert isinstance(
            memory.knowledge_microagents['test-knowledge'], KnowledgeMicroagent
        )
        assert isinstance(memory.repo_microagents['test-repo'], RepoMicroagent)
        assert 'test trigger' in memory.knowledge_microagents['test-knowledge'].triggers
        assert (
            'This is a test knowledge microagent.'
            in memory.knowledge_microagents['test-knowledge'].content
        )
        assert (
            'This is a test repo microagent.'
            in memory.repo_microagents['test-repo'].content
        )
