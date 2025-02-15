"""Tests for the microagent system."""

import tempfile
from pathlib import Path

import pytest

from openhands.core.exceptions import MicroAgentValidationError
from openhands.microagent import (
    BaseMicroAgent,
    KnowledgeMicroAgent,
    MicroAgentMetadata,
    MicroAgentType,
    RepoMicroAgent,
    TaskMicroAgent,
    load_microagents_from_dir,
)

CONTENT = (
    '# dummy header\n' 'dummy content\n' '## dummy subheader\n' 'dummy subcontent\n'
)


def test_legacy_micro_agent_load(tmp_path):
    """Test loading of legacy microagents."""
    legacy_file = tmp_path / '.openhands_instructions'
    legacy_file.write_text(CONTENT)

    micro_agent = BaseMicroAgent.load(legacy_file)
    assert isinstance(micro_agent, RepoMicroAgent)
    assert micro_agent.name == 'repo_legacy'
    assert micro_agent.content == CONTENT
    assert micro_agent.type == MicroAgentType.REPO_KNOWLEDGE


@pytest.fixture
def temp_microagents_dir():
    """Create a temporary directory with test microagents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Create test knowledge agent
        knowledge_agent = """---
name: test_knowledge_agent
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - test
  - pytest
---

# Test Guidelines

Testing best practices and guidelines.
"""
        (root / 'knowledge.md').write_text(knowledge_agent)

        # Create test repo agent
        repo_agent = """---
name: test_repo_agent
type: repo
version: 1.0.0
agent: CodeActAgent
---

# Test Repository Agent

Repository-specific test instructions.
"""
        (root / 'repo.md').write_text(repo_agent)

        # Create test task agent
        task_agent = """---
name: test_task
type: task
version: 1.0.0
agent: CodeActAgent
---

# Test Task

Test task content
"""
        (root / 'task.md').write_text(task_agent)

        yield root


def test_knowledge_agent():
    """Test knowledge agent functionality."""
    agent = KnowledgeMicroAgent(
        name='test',
        content='Test content',
        metadata=MicroAgentMetadata(
            name='test', type=MicroAgentType.KNOWLEDGE, triggers=['test', 'pytest']
        ),
        source='test.md',
        type=MicroAgentType.KNOWLEDGE,
    )

    assert agent.match_trigger('running a test') == 'test'
    assert agent.match_trigger('using pytest') == 'test'
    assert agent.match_trigger('no match here') is None
    assert agent.triggers == ['test', 'pytest']


def test_load_microagents(temp_microagents_dir):
    """Test loading microagents from directory."""
    repo_agents, knowledge_agents, task_agents = load_microagents_from_dir(
        temp_microagents_dir
    )

    # Check knowledge agents
    assert len(knowledge_agents) == 1
    agent = knowledge_agents['test_knowledge_agent']
    assert isinstance(agent, KnowledgeMicroAgent)
    assert 'test' in agent.triggers

    # Check repo agents
    assert len(repo_agents) == 1
    agent = repo_agents['test_repo_agent']
    assert isinstance(agent, RepoMicroAgent)

    # Check task agents
    assert len(task_agents) == 1
    agent = task_agents['test_task']
    assert isinstance(agent, TaskMicroAgent)


def test_invalid_agent_type(temp_microagents_dir):
    """Test loading agent with invalid type."""
    invalid_agent = """---
name: test_invalid
type: invalid
version: 1.0.0
agent: CodeActAgent
---

Invalid agent content
"""
    (temp_microagents_dir / 'invalid.md').write_text(invalid_agent)

    with pytest.raises(MicroAgentValidationError):
        BaseMicroAgent.load(temp_microagents_dir / 'invalid.md')


def test_load_microagents_with_nested_dirs(temp_microagents_dir):
    """Test loading microagents from nested directories."""
    # Create nested knowledge agent
    nested_dir = temp_microagents_dir / 'nested' / 'dir'
    nested_dir.mkdir(parents=True)
    nested_agent = """---
name: nested_knowledge_agent
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - nested
---

# Nested Test Guidelines

Testing nested directory loading.
"""
    (nested_dir / 'nested.md').write_text(nested_agent)

    repo_agents, knowledge_agents, task_agents = load_microagents_from_dir(
        temp_microagents_dir
    )

    # Check that we can find the nested agent
    assert len(knowledge_agents) == 2  # Original + nested
    agent = knowledge_agents['nested_knowledge_agent']
    assert isinstance(agent, KnowledgeMicroAgent)
    assert 'nested' in agent.triggers


def test_load_microagents_with_trailing_slashes(temp_microagents_dir):
    """Test loading microagents when directory paths have trailing slashes."""
    # Create a directory with trailing slash
    knowledge_dir = temp_microagents_dir / 'knowledge/'
    knowledge_dir.mkdir(exist_ok=True)
    knowledge_agent = """---
name: trailing_knowledge_agent
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - trailing
---

# Trailing Slash Test

Testing loading with trailing slashes.
"""
    (knowledge_dir / 'trailing.md').write_text(knowledge_agent)

    repo_agents, knowledge_agents, task_agents = load_microagents_from_dir(
        str(temp_microagents_dir) + '/'  # Add trailing slash to test
    )

    # Check that we can find the agent despite trailing slashes
    assert len(knowledge_agents) == 2  # Original + trailing
    agent = knowledge_agents['trailing_knowledge_agent']
    assert isinstance(agent, KnowledgeMicroAgent)
    assert 'trailing' in agent.triggers
