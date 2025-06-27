"""Tests for user directory microagent loading."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.microagent import KnowledgeMicroagent, MicroagentType, RepoMicroagent
from openhands.storage import get_file_store


@pytest.fixture
def temp_user_microagents_dir():
    """Create a temporary directory to simulate ~/.openhands/microagents/."""
    with tempfile.TemporaryDirectory() as temp_dir:
        user_dir = Path(temp_dir)

        # Create test knowledge agent
        knowledge_agent = """---
name: user_knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - user-test
  - personal
---

# User Knowledge Agent

Personal knowledge and guidelines.
"""
        (user_dir / 'user_knowledge.md').write_text(knowledge_agent)

        # Create test repo agent
        repo_agent = """---
name: user_repo
version: 1.0.0
agent: CodeActAgent
---

# User Repository Agent

Personal repository-specific instructions.
"""
        (user_dir / 'user_repo.md').write_text(repo_agent)

        yield user_dir


def test_user_microagents_loading(temp_user_microagents_dir):
    """Test that user microagents are loaded from ~/.openhands/microagents/."""
    with patch(
        'openhands.memory.memory.USER_MICROAGENTS_DIR', str(temp_user_microagents_dir)
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create event stream and memory
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)
            memory = Memory(event_stream, 'test_sid')

            # Check that user microagents were loaded
            assert 'user_knowledge' in memory.knowledge_microagents
            assert 'user_repo' in memory.repo_microagents

            # Verify the loaded agents
            user_knowledge = memory.knowledge_microagents['user_knowledge']
            assert isinstance(user_knowledge, KnowledgeMicroagent)
            assert user_knowledge.type == MicroagentType.KNOWLEDGE
            assert 'user-test' in user_knowledge.triggers
            assert 'personal' in user_knowledge.triggers

            user_repo = memory.repo_microagents['user_repo']
            assert isinstance(user_repo, RepoMicroagent)
            assert user_repo.type == MicroagentType.REPO_KNOWLEDGE


def test_user_microagents_directory_creation():
    """Test that user microagents directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_dir = Path(temp_dir) / 'non_existent' / 'microagents'

        with patch(
            'openhands.memory.memory.USER_MICROAGENTS_DIR', str(non_existent_dir)
        ):
            with tempfile.TemporaryDirectory() as temp_store_dir:
                # Create event stream and memory
                file_store = get_file_store('local', temp_store_dir)
                event_stream = EventStream('test', file_store)
                Memory(event_stream, 'test_sid')

                # Check that the directory was created
                assert non_existent_dir.exists()
                assert non_existent_dir.is_dir()


def test_user_microagents_override_global():
    """Test that user microagents can override global ones with the same name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        user_dir = Path(temp_dir)

        # Create a user microagent with the same name as a global one
        # (assuming there's a global 'github' microagent)
        github_agent = """---
name: github
version: 1.0.0
agent: CodeActAgent
triggers:
  - github
  - git
---

# Personal GitHub Agent

My personal GitHub workflow and preferences.
"""
        (user_dir / 'github.md').write_text(github_agent)

        with patch('openhands.memory.memory.USER_MICROAGENTS_DIR', str(user_dir)):
            with tempfile.TemporaryDirectory() as temp_store_dir:
                # Create event stream and memory
                file_store = get_file_store('local', temp_store_dir)
                event_stream = EventStream('test', file_store)
                memory = Memory(event_stream, 'test_sid')

                # Check that the user microagent is loaded
                if 'github' in memory.knowledge_microagents:
                    github_microagent = memory.knowledge_microagents['github']
                    # The user version should contain our personal content
                    assert 'My personal GitHub workflow' in github_microagent.content


def test_user_microagents_loading_error_handling():
    """Test error handling when user microagents directory has issues."""
    with tempfile.TemporaryDirectory() as temp_dir:
        user_dir = Path(temp_dir)

        # Create an invalid microagent file
        invalid_agent = """---
name: invalid
type: invalid_type
---

# Invalid Agent
"""
        (user_dir / 'invalid.md').write_text(invalid_agent)

        with patch('openhands.memory.memory.USER_MICROAGENTS_DIR', str(user_dir)):
            with tempfile.TemporaryDirectory() as temp_store_dir:
                # Create event stream and memory - should not crash
                file_store = get_file_store('local', temp_store_dir)
                event_stream = EventStream('test', file_store)
                memory = Memory(event_stream, 'test_sid')

                # Memory should still be created despite the invalid microagent
                assert memory is not None
                # The invalid microagent should not be loaded
                assert 'invalid' not in memory.knowledge_microagents
                assert 'invalid' not in memory.repo_microagents


def test_user_microagents_empty_directory():
    """Test behavior when user microagents directory is empty."""
    with tempfile.TemporaryDirectory() as temp_dir:
        empty_dir = Path(temp_dir)

        with patch('openhands.memory.memory.USER_MICROAGENTS_DIR', str(empty_dir)):
            with tempfile.TemporaryDirectory() as temp_store_dir:
                # Create event stream and memory
                file_store = get_file_store('local', temp_store_dir)
                event_stream = EventStream('test', file_store)
                memory = Memory(event_stream, 'test_sid')

                # Memory should be created successfully
                assert memory is not None
                # No user microagents should be loaded, but global ones might be
                # (we can't assert the exact count since global microagents may exist)


def test_user_microagents_nested_directories(temp_user_microagents_dir):
    """Test loading user microagents from nested directories."""
    # Create nested microagent
    nested_dir = temp_user_microagents_dir / 'personal' / 'tools'
    nested_dir.mkdir(parents=True)

    nested_agent = """---
name: personal_tool
version: 1.0.0
agent: CodeActAgent
triggers:
  - personal-tool
---

# Personal Tool Agent

My personal development tools and workflows.
"""
    (nested_dir / 'tool.md').write_text(nested_agent)

    with patch(
        'openhands.memory.memory.USER_MICROAGENTS_DIR', str(temp_user_microagents_dir)
    ):
        with tempfile.TemporaryDirectory() as temp_store_dir:
            # Create event stream and memory
            file_store = get_file_store('local', temp_store_dir)
            event_stream = EventStream('test', file_store)
            memory = Memory(event_stream, 'test_sid')

            # Check that nested microagent was loaded
            # The name should be derived from the relative path
            assert 'personal/tools/tool' in memory.knowledge_microagents

            nested_microagent = memory.knowledge_microagents['personal/tools/tool']
            assert isinstance(nested_microagent, KnowledgeMicroagent)
            assert 'personal-tool' in nested_microagent.triggers
