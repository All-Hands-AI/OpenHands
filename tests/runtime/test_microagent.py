"""Tests for microagent loading in runtime."""

from pathlib import Path

from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.microagent import KnowledgeMicroAgent, RepoMicroAgent, TaskMicroAgent


def _create_test_microagents(test_dir: str):
    """Create test microagent files in the given directory."""
    microagents_dir = Path(test_dir) / '.openhands' / 'microagents'
    microagents_dir.mkdir(parents=True, exist_ok=True)

    # Create test knowledge agent
    knowledge_dir = microagents_dir / 'knowledge'
    knowledge_dir.mkdir(exist_ok=True)
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
    (knowledge_dir / 'knowledge.md').write_text(knowledge_agent)

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
    (microagents_dir / 'repo.md').write_text(repo_agent)

    # Create test task agent in a nested directory
    task_dir = microagents_dir / 'tasks' / 'nested'
    task_dir.mkdir(parents=True, exist_ok=True)
    task_agent = """---
name: test_task
type: task
version: 1.0.0
agent: CodeActAgent
---

# Test Task

Test task content
"""
    (task_dir / 'task.md').write_text(task_agent)

    # Create legacy repo instructions
    legacy_instructions = """# Legacy Instructions

These are legacy repository instructions.
"""
    (Path(test_dir) / '.openhands_instructions').write_text(legacy_instructions)


def test_load_microagents_with_trailing_slashes(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test loading microagents when directory paths have trailing slashes."""
    # Create test files
    _create_test_microagents(temp_dir)
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents
        loaded_agents = runtime.get_microagents_from_selected_repo(None)

        # Verify all agents are loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroAgent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroAgent)]
        task_agents = [a for a in loaded_agents if isinstance(a, TaskMicroAgent)]

        # Check knowledge agents
        assert len(knowledge_agents) == 1
        agent = knowledge_agents[0]
        assert agent.name == 'test_knowledge_agent'
        assert 'test' in agent.triggers
        assert 'pytest' in agent.triggers

        # Check repo agents (including legacy)
        assert len(repo_agents) == 2  # repo.md + .openhands_instructions
        repo_names = {a.name for a in repo_agents}
        assert 'test_repo_agent' in repo_names
        assert 'repo_legacy' in repo_names

        # Check task agents
        assert len(task_agents) == 1
        agent = task_agents[0]
        assert agent.name == 'test_task'

    finally:
        _close_test_runtime(runtime)


def test_load_microagents_with_selected_repo(temp_dir, runtime_cls, run_as_openhands):
    """Test loading microagents from a selected repository."""
    # Create test files in a repository-like structure
    repo_dir = Path(temp_dir) / 'OpenHands'
    repo_dir.mkdir(parents=True)
    _create_test_microagents(str(repo_dir))

    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents with selected repository
        loaded_agents = runtime.get_microagents_from_selected_repo(
            'All-Hands-AI/OpenHands'
        )

        # Verify all agents are loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroAgent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroAgent)]
        task_agents = [a for a in loaded_agents if isinstance(a, TaskMicroAgent)]

        # Check knowledge agents
        assert len(knowledge_agents) == 1
        agent = knowledge_agents[0]
        assert agent.name == 'test_knowledge_agent'
        assert 'test' in agent.triggers
        assert 'pytest' in agent.triggers

        # Check repo agents (including legacy)
        assert len(repo_agents) == 2  # repo.md + .openhands_instructions
        repo_names = {a.name for a in repo_agents}
        assert 'test_repo_agent' in repo_names
        assert 'repo_legacy' in repo_names

        # Check task agents
        assert len(task_agents) == 1
        agent = task_agents[0]
        assert agent.name == 'test_task'

    finally:
        _close_test_runtime(runtime)


def test_load_microagents_with_missing_files(temp_dir, runtime_cls, run_as_openhands):
    """Test loading microagents when some files are missing."""
    # Create only repo.md, no other files
    microagents_dir = Path(temp_dir) / '.openhands' / 'microagents'
    microagents_dir.mkdir(parents=True, exist_ok=True)

    repo_agent = """---
name: test_repo_agent
type: repo
version: 1.0.0
agent: CodeActAgent
---

# Test Repository Agent

Repository-specific test instructions.
"""
    (microagents_dir / 'repo.md').write_text(repo_agent)

    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents
        loaded_agents = runtime.get_microagents_from_selected_repo(None)

        # Verify only repo agent is loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroAgent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroAgent)]
        task_agents = [a for a in loaded_agents if isinstance(a, TaskMicroAgent)]

        assert len(knowledge_agents) == 0
        assert len(repo_agents) == 1
        assert len(task_agents) == 0

        agent = repo_agents[0]
        assert agent.name == 'test_repo_agent'

    finally:
        _close_test_runtime(runtime)
