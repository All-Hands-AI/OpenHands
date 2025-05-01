"""Tests for microagent loading in runtime."""

import tempfile
from pathlib import Path

from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.microagent.microagent import (
    BaseMicroagent,
    RepoMicroagent,
    KnowledgeMicroagent,
    TaskMicroagent,
)
from openhands.microagent.types import MicroagentType


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
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents
        loaded_agents = runtime.get_microagents_from_selected_repo(None)

        # Verify all agents are loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroagent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroagent)]

        # Check knowledge agents
        assert len(knowledge_agents) == 1
        agent = knowledge_agents[0]
        assert agent.name == 'knowledge/knowledge'
        assert 'test' in agent.triggers
        assert 'pytest' in agent.triggers

        # Check repo agents (including legacy)
        assert len(repo_agents) == 2  # repo.md + .openhands_instructions
        repo_names = {a.name for a in repo_agents}
        assert 'repo' in repo_names
        assert 'repo_legacy' in repo_names

    finally:
        _close_test_runtime(runtime)


def test_load_microagents_with_selected_repo(temp_dir, runtime_cls, run_as_openhands):
    """Test loading microagents from a selected repository."""
    # Create test files in a repository-like structure
    repo_dir = Path(temp_dir) / 'OpenHands'
    repo_dir.mkdir(parents=True)
    _create_test_microagents(str(repo_dir))

    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents with selected repository
        loaded_agents = runtime.get_microagents_from_selected_repo(
            'All-Hands-AI/OpenHands'
        )

        # Verify all agents are loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroagent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroagent)]

        # Check knowledge agents
        assert len(knowledge_agents) == 1
        agent = knowledge_agents[0]
        assert agent.name == 'knowledge/knowledge'
        assert 'test' in agent.triggers
        assert 'pytest' in agent.triggers

        # Check repo agents (including legacy)
        assert len(repo_agents) == 2  # repo.md + .openhands_instructions
        repo_names = {a.name for a in repo_agents}
        assert 'repo' in repo_names
        assert 'repo_legacy' in repo_names

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

    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Load microagents
        loaded_agents = runtime.get_microagents_from_selected_repo(None)

        # Verify only repo agent is loaded
        knowledge_agents = [
            a for a in loaded_agents if isinstance(a, KnowledgeMicroagent)
        ]
        repo_agents = [a for a in loaded_agents if isinstance(a, RepoMicroagent)]

        assert len(knowledge_agents) == 0
        assert len(repo_agents) == 1

        agent = repo_agents[0]
        assert agent.name == 'repo'

    finally:
        _close_test_runtime(runtime)


def test_task_microagent_creation():
    """Test that a TaskMicroagent is created correctly."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent with a variable: ${test_var}.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.type == MicroagentType.TASK
        assert agent.name == 'test_task'
        assert '/test_task' in agent.triggers
        assert "If the user didn't provide any of these variables" in agent.content


def test_task_microagent_variable_extraction():
    """Test that variables are correctly extracted from the content."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: var1
    description: "Variable 1"
---

This is a test with variables: ${var1}, ${var2}, and ${var3}.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        variables = agent.extract_variables(agent.content)
        assert set(variables) == {'var1', 'var2', 'var3'}
        assert agent.requires_user_input()


def test_knowledge_microagent_no_prompt():
    """Test that a regular KnowledgeMicroagent doesn't get the prompt."""
    content = """---
name: test_knowledge
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- test_knowledge
---

This is a test knowledge microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, KnowledgeMicroagent)
        assert agent.type == MicroagentType.KNOWLEDGE
        assert "If the user didn't provide any of these variables" not in agent.content


def test_task_microagent_trigger_addition():
    """Test that a trigger is added if not present."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert '/test_task' in agent.triggers


def test_task_microagent_no_duplicate_trigger():
    """Test that a trigger is not duplicated if already present."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
- another_trigger
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.triggers.count('/test_task') == 1  # No duplicates
        assert len(agent.triggers) == 2
        assert 'another_trigger' in agent.triggers
        assert '/test_task' in agent.triggers


def test_task_microagent_match_trigger():
    """Test that a task microagent matches its trigger correctly."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.match_trigger('/test_task') == '/test_task'
        assert (
            agent.match_trigger('  /test_task  ') == '/test_task'
        )  # Whitespace is trimmed
        assert (
            agent.match_trigger('This contains /test_task') is None
        )  # Not an exact match
        assert agent.match_trigger('/other_task') is None
