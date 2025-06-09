"""Tests for the microagent system."""

import tempfile
from pathlib import Path

import pytest

from openhands.microagent import (
    BaseMicroagent,
    KnowledgeMicroagent,
    MicroagentMetadata,
    MicroagentType,
    RepoMicroagent,
    load_microagents_from_dir,
)

CONTENT = '# dummy header\ndummy content\n## dummy subheader\ndummy subcontent\n'


def test_legacy_micro_agent_load(tmp_path):
    """Test loading of legacy microagents."""
    legacy_file = tmp_path / '.openhands_instructions'
    legacy_file.write_text(CONTENT)

    # Pass microagent_dir (tmp_path in this case) to load
    micro_agent = BaseMicroagent.load(legacy_file, tmp_path)
    assert isinstance(micro_agent, RepoMicroagent)
    assert micro_agent.name == 'repo_legacy'  # Legacy name is hardcoded
    assert micro_agent.content == CONTENT
    assert micro_agent.type == MicroagentType.REPO_KNOWLEDGE


@pytest.fixture
def temp_microagents_dir():
    """Create a temporary directory with test microagents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Create test knowledge agent (type inferred from triggers)
        knowledge_agent = """---
# type: knowledge
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

        # Create test repo agent (type inferred from lack of triggers)
        repo_agent = """---
# type: repo
version: 1.0.0
agent: CodeActAgent
---

# Test Repository Agent

Repository-specific test instructions.
"""
        (root / 'repo.md').write_text(repo_agent)

        yield root


def test_knowledge_agent():
    """Test knowledge agent functionality."""
    # Note: We still pass type to the constructor here, as it expects it.
    # The loader infers the type before calling the constructor.
    agent = KnowledgeMicroagent(
        name='test',
        content='Test content',
        metadata=MicroagentMetadata(name='test', triggers=['test', 'pytest']),
        source='test.md',
        type=MicroagentType.KNOWLEDGE,  # Constructor still needs type
    )

    assert agent.match_trigger('running a test') == 'test'
    assert agent.match_trigger('using pytest') == 'test'
    assert agent.match_trigger('no match here') is None
    assert agent.triggers == ['test', 'pytest']


def test_load_microagents(temp_microagents_dir):
    """Test loading microagents from directory."""
    repo_agents, knowledge_agents = load_microagents_from_dir(temp_microagents_dir)

    # Check knowledge agents (name derived from filename: knowledge.md -> 'knowledge')
    assert len(knowledge_agents) == 1
    agent_k = knowledge_agents['knowledge']
    assert isinstance(agent_k, KnowledgeMicroagent)
    assert agent_k.type == MicroagentType.KNOWLEDGE  # Check inferred type
    assert 'test' in agent_k.triggers

    # Check repo agents (name derived from filename: repo.md -> 'repo')
    assert len(repo_agents) == 1
    agent_r = repo_agents['repo']
    assert isinstance(agent_r, RepoMicroagent)
    assert agent_r.type == MicroagentType.REPO_KNOWLEDGE  # Check inferred type


def test_load_microagents_with_nested_dirs(temp_microagents_dir):
    """Test loading microagents from nested directories."""
    # Create nested knowledge agent
    nested_dir = temp_microagents_dir / 'nested' / 'dir'
    nested_dir.mkdir(parents=True)
    nested_agent = """---
# type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - nested
---

# Nested Test Guidelines

Testing nested directory loading.
"""
    (nested_dir / 'nested.md').write_text(nested_agent)

    repo_agents, knowledge_agents = load_microagents_from_dir(temp_microagents_dir)

    # Check that we can find the nested agent (name derived from path: nested/dir/nested.md -> 'nested/dir/nested')
    assert (
        len(knowledge_agents) == 2
    )  # Original ('knowledge') + nested ('nested/dir/nested')
    agent_n = knowledge_agents['nested/dir/nested']
    assert isinstance(agent_n, KnowledgeMicroagent)
    assert agent_n.type == MicroagentType.KNOWLEDGE  # Check inferred type
    assert 'nested' in agent_n.triggers


def test_load_microagents_with_trailing_slashes(temp_microagents_dir):
    """Test loading microagents when directory paths have trailing slashes."""
    # Create a directory with trailing slash
    knowledge_dir = temp_microagents_dir / 'test_knowledge/'
    knowledge_dir.mkdir(exist_ok=True)
    knowledge_agent = """---
# type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - trailing
---

# Trailing Slash Test

Testing loading with trailing slashes.
"""
    (knowledge_dir / 'trailing.md').write_text(knowledge_agent)

    repo_agents, knowledge_agents = load_microagents_from_dir(
        str(temp_microagents_dir) + '/'  # Add trailing slash to test
    )

    # Check that we can find the agent despite trailing slashes (name derived from path: test_knowledge/trailing.md -> 'test_knowledge/trailing')
    assert (
        len(knowledge_agents) == 2
    )  # Original ('knowledge') + trailing ('test_knowledge/trailing')
    agent_t = knowledge_agents['test_knowledge/trailing']
    assert isinstance(agent_t, KnowledgeMicroagent)
    assert agent_t.type == MicroagentType.KNOWLEDGE  # Check inferred type
    assert 'trailing' in agent_t.triggers


def test_invalid_microagent_type(temp_microagents_dir):
    """Test loading a microagent with an invalid type."""
    # Create a microagent with an invalid type
    invalid_agent = """---
name: invalid_type_agent
type: invalid_type
version: 1.0.0
agent: CodeActAgent
triggers:
  - test
---

# Invalid Type Test

This microagent has an invalid type.
"""
    invalid_file = temp_microagents_dir / 'invalid_type.md'
    invalid_file.write_text(invalid_agent)

    # Attempt to load the microagent should raise a MicroagentValidationError
    from openhands.core.exceptions import MicroagentValidationError

    with pytest.raises(MicroagentValidationError) as excinfo:
        load_microagents_from_dir(temp_microagents_dir)

    # Check that the error message contains helpful information
    error_msg = str(excinfo.value)
    assert 'invalid_type.md' in error_msg
    assert 'Invalid "type" value: "invalid_type"' in error_msg
    assert 'Valid types are:' in error_msg
    assert '"knowledge"' in error_msg
    assert '"repo"' in error_msg
    assert '"task"' in error_msg
