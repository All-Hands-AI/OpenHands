"""Tests for repository name trigger functionality in microagents."""

import tempfile
from pathlib import Path

import pytest

from openhands.microagent import (
    KnowledgeMicroagent,
    MicroagentMetadata,
    MicroagentType,
    load_microagents_from_dir,
)


def test_repo_trigger_microagent():
    """Test microagent with repository name triggers."""
    # Create a microagent with repo_triggers
    agent = KnowledgeMicroagent(
        name='repo_trigger_test',
        content='Test content for repo-specific microagent',
        metadata=MicroagentMetadata(
            name='repo_trigger_test',
            triggers=['test'],
            repo_triggers=['test-repo', 'another-repo'],
        ),
        source='test.md',
        type=MicroagentType.KNOWLEDGE,
    )

    # Test regular trigger matching
    assert agent.match_trigger('running a test') == 'test'

    # Test repo trigger matching
    assert agent.match_trigger('unrelated message', 'test-repo') == 'repo:test-repo'
    assert (
        agent.match_trigger('unrelated message', 'another-repo') == 'repo:another-repo'
    )

    # Test no match
    assert agent.match_trigger('unrelated message', 'different-repo') is None

    # Test case insensitivity for repo triggers
    assert agent.match_trigger('unrelated message', 'TEST-REPO') == 'repo:test-repo'


@pytest.fixture
def temp_microagents_dir_with_repo_triggers():
    """Create a temporary directory with test microagents including repo triggers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Create test knowledge agent with repo triggers
        knowledge_agent = """---
# type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - test
  - pytest
repo_triggers:
  - test-repo
  - another-repo
---

# Test Guidelines with Repo Triggers

Testing best practices and guidelines for specific repositories.
"""
        (root / 'knowledge.md').write_text(knowledge_agent)

        yield root


def test_load_microagents_with_repo_triggers(temp_microagents_dir_with_repo_triggers):
    """Test loading microagents with repository triggers from directory."""
    repo_agents, knowledge_agents = load_microagents_from_dir(
        temp_microagents_dir_with_repo_triggers
    )

    # Check knowledge agents
    assert len(knowledge_agents) == 1
    agent_k = knowledge_agents['knowledge']
    assert isinstance(agent_k, KnowledgeMicroagent)
    assert agent_k.type == MicroagentType.KNOWLEDGE

    # Check triggers
    assert 'test' in agent_k.triggers
    assert 'pytest' in agent_k.triggers

    # Check repo triggers
    assert 'test-repo' in agent_k.repo_triggers
    assert 'another-repo' in agent_k.repo_triggers

    # Test trigger matching
    assert agent_k.match_trigger('running a test') == 'test'
    assert agent_k.match_trigger('unrelated message', 'test-repo') == 'repo:test-repo'
