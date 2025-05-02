import os
import shutil
import tempfile
from unittest import mock

import pytest

from openhands.memory.memory import Memory
from openhands.microagent import KnowledgeMicroagent, RepoMicroagent


class TestUserGlobalMicroagents:
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

    def test_user_global_microagents_directory_creation(self, mock_event_stream):
        """Test that the user global microagents directory is created if it doesn't exist."""
        # Mock the expanduser to return a non-existent path
        test_path = os.path.join(tempfile.gettempdir(), f'openhands_test_{os.getpid()}')

        # Make sure the directory doesn't exist
        if os.path.exists(test_path):
            shutil.rmtree(test_path)

        with mock.patch('os.path.expanduser', return_value=test_path):
            with mock.patch(
                'openhands.memory.memory.USER_GLOBAL_MICROAGENTS_DIR', test_path
            ):
                # Initialize Memory which should create the directory
                memory = Memory(mock_event_stream, 'test_sid')

                # Check that the directory was created
                assert os.path.exists(test_path)

                # Clean up
                shutil.rmtree(test_path)

    def test_load_user_global_microagents(
        self, mock_event_stream, temp_user_microagents_dir
    ):
        """Test that user global microagents are loaded correctly."""
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

        # Mock the expanduser to return our temp directory
        with mock.patch('os.path.expanduser', return_value=temp_user_microagents_dir):
            with mock.patch(
                'openhands.memory.memory.USER_GLOBAL_MICROAGENTS_DIR',
                temp_user_microagents_dir,
            ):
                # Initialize Memory which should load our test microagents
                memory = Memory(mock_event_stream, 'test_sid')

                # Check that the microagents were loaded
                assert 'test-knowledge' in memory.knowledge_microagents
                assert 'test-repo' in memory.repo_microagents

                # Verify the content
                assert isinstance(
                    memory.knowledge_microagents['test-knowledge'], KnowledgeMicroagent
                )
                assert isinstance(memory.repo_microagents['test-repo'], RepoMicroagent)
                assert (
                    'test trigger'
                    in memory.knowledge_microagents['test-knowledge'].triggers
                )
                assert (
                    'This is a test knowledge microagent.'
                    in memory.knowledge_microagents['test-knowledge'].content
                )
                assert (
                    'This is a test repo microagent.'
                    in memory.repo_microagents['test-repo'].content
                )

    def test_microagent_trigger_matching(
        self, mock_event_stream, temp_user_microagents_dir
    ):
        """Test that user global microagents can be triggered by keywords."""
        # Create a test knowledge microagent
        knowledge_content = """---
name: test-knowledge
type: knowledge
triggers:
  - test trigger
  - another trigger
---
# Test Knowledge
This is a test knowledge microagent.
"""
        knowledge_path = os.path.join(temp_user_microagents_dir, 'test-knowledge.md')
        with open(knowledge_path, 'w') as f:
            f.write(knowledge_content)

        # Mock the expanduser to return our temp directory
        with mock.patch('os.path.expanduser', return_value=temp_user_microagents_dir):
            with mock.patch(
                'openhands.memory.memory.USER_GLOBAL_MICROAGENTS_DIR',
                temp_user_microagents_dir,
            ):
                # Initialize Memory which should load our test microagents
                memory = Memory(mock_event_stream, 'test_sid')

                # Test trigger matching
                microagent_knowledge = memory._find_microagent_knowledge(
                    'I need help with test trigger please'
                )
                assert len(microagent_knowledge) == 1
                assert microagent_knowledge[0].name == 'test-knowledge'
                assert microagent_knowledge[0].trigger == 'test trigger'

                # Test another trigger
                microagent_knowledge = memory._find_microagent_knowledge(
                    'Can you help with another trigger?'
                )
                assert len(microagent_knowledge) == 1
                assert microagent_knowledge[0].name == 'test-knowledge'
                assert microagent_knowledge[0].trigger == 'another trigger'

                # Test no match
                microagent_knowledge = memory._find_microagent_knowledge(
                    "This doesn't match any trigger"
                )
                assert len(microagent_knowledge) == 0
