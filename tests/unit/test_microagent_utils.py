"""Tests for the microagent system."""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

import openhands.agenthub  # noqa: F401
from openhands.core.microagents import (
    InputValidation,
    KnowledgeAgent,
    MicroAgent,
    MicroAgentHub,
    TaskAgent,
    TaskInput,
    TaskType,
    TriggerType,
)

CONTENT = (
    '# dummy header\n' 'dummy content\n' '## dummy subheader\n' 'dummy subcontent\n'
)


def test_legacy_micro_agent_load(tmp_path, monkeypatch: MonkeyPatch):
    """Test loading of legacy microagents."""
    with open(os.path.join(tmp_path, 'dummy.md'), 'w') as f:
        f.write(
            (
                '---\n'
                'name: dummy\n'
                'agent: CodeActAgent\n'
                'require_env_var:\n'
                '  SANDBOX_OPENHANDS_TEST_ENV_VAR: "Set this environment variable for testing purposes"\n'
                '---\n' + CONTENT
            )
        )

    # Patch the required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    micro_agent = MicroAgent.from_markdown(os.path.join(tmp_path, 'dummy.md'))
    assert micro_agent is not None
    assert micro_agent.content == CONTENT.strip()


@pytest.fixture
def temp_microagents_dir():
    """Create a temporary directory with test microagents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure
        root = Path(temp_dir)
        (root / 'knowledge').mkdir(parents=True)
        (root / 'tasks').mkdir(parents=True)

        # Create test agents
        repo_agent = """---
name: test_repo_agent
version: 1.0.0
author: test
agent: CodeActAgent
category: testing
trigger_type: repository
trigger_pattern: test-org/*
priority: 100
---

# Test Repository Agent

Repository-specific test instructions.
"""
        with open(root / 'knowledge/repo_test.md', 'w') as f:
            f.write(repo_agent)

        keyword_agent = """---
name: test_keyword_agent
version: 1.0.0
author: test
agent: CodeActAgent
category: testing
trigger_type: keyword
triggers:
  - test
  - pytest
file_patterns:
  - "*.py"
  - "*.test.js"
require_env_var:
  SANDBOX_OPENHANDS_TEST_ENV_VAR: "Set this environment variable for testing purposes"
---

# Test Guidelines

Testing best practices and guidelines.
"""
        with open(root / 'knowledge/testing.md', 'w') as f:
            f.write(keyword_agent)

        task_agent = """---
name: test_task
version: 1.0.0
author: test
agent: CodeActAgent
category: testing
task_type: workflow
inputs:
  - name: VAR1
    description: First variable
    type: string
    required: true
  - name: VAR2
    description: Second variable
    type: string
    required: false
    default: default
---

# Test Task

Testing ${VAR1} and ${VAR2}...
"""
        with open(root / 'tasks/test.md', 'w') as f:
            f.write(task_agent)

        yield root


def test_knowledge_agent_validation(monkeypatch: MonkeyPatch):
    """Test validation of knowledge agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    # Test repository agent validation
    with pytest.raises(ValidationError):
        # Missing trigger_pattern for repository agent
        KnowledgeAgent(
            name='test',
            version='1.0.0',
            author='test',
            agent='CodeActAgent',
            category='testing',
            trigger_type=TriggerType.REPOSITORY,
            content='Test',
        )

    # Test keyword agent validation
    with pytest.raises(ValidationError):
        # Missing triggers for keyword agent
        KnowledgeAgent(
            name='test',
            version='1.0.0',
            author='test',
            agent='CodeActAgent',
            category='testing',
            trigger_type=TriggerType.KEYWORD,
            content='Test',
        )

    # Valid repository agent
    agent = KnowledgeAgent(
        name='test',
        version='1.0.0',
        author='test',
        agent='CodeActAgent',
        category='testing',
        trigger_type=TriggerType.REPOSITORY,
        trigger_pattern='org/*',
        content='Test',
    )
    assert agent.trigger_pattern == 'org/*'

    # Valid keyword agent
    agent = KnowledgeAgent(
        name='test',
        version='1.0.0',
        author='test',
        agent='CodeActAgent',
        category='testing',
        trigger_type=TriggerType.KEYWORD,
        triggers=['test'],
        content='Test',
    )
    assert agent.triggers == ['test']


def test_task_agent_validation():
    """Test validation of task agents."""
    # Test input validation
    input1 = TaskInput(
        name='test',
        description='Test input',
        type='string',
        required=True,
        validation=InputValidation(pattern=r'^test.*'),
    )
    assert input1.validation.pattern == r'^test.*'

    # Test task agent
    agent = TaskAgent(
        name='test',
        version='1.0.0',
        author='test',
        agent='CodeActAgent',
        category='testing',
        task_type=TaskType.WORKFLOW,
        content='Test ${VAR}',
        inputs=[input1],
    )
    assert '${VAR}' in agent.content
    assert len(agent.inputs) == 1


def test_microagent_hub_loading(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test loading of microagents from directory."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Check repository agents
    assert len(hub.repo_agents) == 1
    agent = hub.repo_agents['test_repo_agent']
    assert agent.trigger_pattern == 'test-org/*'
    assert agent.priority == 100

    # Check keyword agents
    assert len(hub.keyword_agents) == 1
    agent = hub.keyword_agents['test_keyword_agent']
    assert 'test' in agent.triggers
    assert '*.py' in agent.file_patterns

    # Check task agents
    assert len(hub.task_agents) == 1
    agent = hub.task_agents['test_task']
    assert agent.task_type == TaskType.WORKFLOW
    assert len(agent.inputs) == 2


def test_repo_agent_matching(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test matching of repository agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test matching repository
    agents = hub.get_repo_agents('test-org/repo1')
    assert len(agents) == 1
    assert agents[0].name == 'test_repo_agent'

    # Test non-matching repository
    agents = hub.get_repo_agents('other-org/repo1')
    assert len(agents) == 0


def test_keyword_agent_matching(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test matching of keyword agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test matching keyword
    agents = hub.get_keyword_agents('Running test with pytest')
    assert len(agents) == 1
    assert agents[0].name == 'test_keyword_agent'

    # Test matching keyword with file pattern
    agents = hub.get_keyword_agents('Running test', 'test.py')
    assert len(agents) == 1

    # Test matching keyword with non-matching file pattern
    agents = hub.get_keyword_agents('Running test', 'test.txt')
    assert len(agents) == 0

    # Test non-matching keyword
    agents = hub.get_keyword_agents('No matches here')
    assert len(agents) == 0


def test_task_processing(temp_microagents_dir):
    """Test processing of tasks."""
    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test with all variables
    result = hub.process_task('test_task', {'VAR1': 'value1', 'VAR2': 'value2'})
    assert 'Testing value1 and value2' in result

    # Test with default value
    result = hub.process_task('test_task', {'VAR1': 'value1'})
    assert 'Testing value1 and default' in result

    # Test missing required variable
    with pytest.raises(ValueError):
        hub.process_task('test_task', {'VAR2': 'value2'})

    # Test non-existent task
    result = hub.process_task('non_existent', {})
    assert result is None


def test_task_listing(temp_microagents_dir):
    """Test listing of task agents."""
    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test listing all tasks
    tasks = hub.list_task_agents()
    assert len(tasks) == 1

    # Test listing by type
    tasks = hub.list_task_agents(TaskType.WORKFLOW)
    assert len(tasks) == 1
    tasks = hub.list_task_agents(TaskType.SNIPPET)
    assert len(tasks) == 0
