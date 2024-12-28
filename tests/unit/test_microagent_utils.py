"""Tests for the microagent system."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from pytest import MonkeyPatch

import openhands.agenthub  # noqa: F401
from openhands.core.microagents import (
    InputValidation,
    KnowledgeAgent,
    MicroAgentHub,
    TemplateAgent,
    TemplateInput,
    TemplateType,
    TriggerType,
)
from openhands.utils.microagent import MicroAgent


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

    micro_agent = MicroAgent(os.path.join(tmp_path, 'dummy.md'))
    assert micro_agent is not None
    assert micro_agent.content == CONTENT.strip()


@pytest.fixture
def temp_microagents_dir():
    """Create a temporary directory with test microagents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure
        root = Path(temp_dir)
        (root / "official/knowledge/repo").mkdir(parents=True)
        (root / "official/knowledge/keyword").mkdir(parents=True)
        (root / "official/templates/workflows").mkdir(parents=True)

        # Create test agents
        repo_agent = {
            "name": "test_repo_agent",
            "version": "1.0.0",
            "author": "test",
            "agent": "CodeActAgent",
            "category": "testing",
            "trigger_type": "repository",
            "trigger_pattern": "test-org/*",
            "priority": 100,
            "description": "Test repo agent",
            "knowledge": "Test repo knowledge",
        }
        with open(root / "official/knowledge/repo/test.yaml", "w") as f:
            yaml.dump(repo_agent, f)

        keyword_agent = {
            "name": "test_keyword_agent",
            "version": "1.0.0",
            "author": "test",
            "agent": "CodeActAgent",
            "category": "testing",
            "trigger_type": "keyword",
            "triggers": ["test", "pytest"],
            "file_patterns": ["*.py", "*.test.js"],
            "description": "Test keyword agent",
            "knowledge": "Test keyword knowledge",
            "require_env_var": {
                "SANDBOX_OPENHANDS_TEST_ENV_VAR": "Set this environment variable for testing purposes"
            },
        }
        with open(root / "official/knowledge/keyword/test.yaml", "w") as f:
            yaml.dump(keyword_agent, f)

        template_agent = {
            "name": "test_template",
            "version": "1.0.0",
            "author": "test",
            "agent": "CodeActAgent",
            "category": "testing",
            "template_type": "workflow",
            "description": "Test template agent",
            "template": "Test ${VAR1} and ${VAR2}",
            "inputs": [
                {
                    "name": "VAR1",
                    "description": "First variable",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "VAR2",
                    "description": "Second variable",
                    "type": "string",
                    "required": False,
                    "default": "default",
                },
            ],
        }
        with open(root / "official/templates/workflows/test.yaml", "w") as f:
            yaml.dump(template_agent, f)

        yield root


def test_knowledge_agent_validation(monkeypatch: MonkeyPatch):
    """Test validation of knowledge agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    # Test repository agent validation
    with pytest.raises(ValidationError):
        # Missing trigger_pattern for repository agent
        KnowledgeAgent(
            name="test",
            version="1.0.0",
            author="test",
            agent="CodeActAgent",
            category="testing",
            trigger_type=TriggerType.REPOSITORY,
            description="Test",
            knowledge="Test",
        )

    # Test keyword agent validation
    with pytest.raises(ValidationError):
        # Missing triggers for keyword agent
        KnowledgeAgent(
            name="test",
            version="1.0.0",
            author="test",
            agent="CodeActAgent",
            category="testing",
            trigger_type=TriggerType.KEYWORD,
            description="Test",
            knowledge="Test",
        )

    # Valid repository agent
    agent = KnowledgeAgent(
        name="test",
        version="1.0.0",
        author="test",
        agent="CodeActAgent",
        category="testing",
        trigger_type=TriggerType.REPOSITORY,
        trigger_pattern="org/*",
        description="Test",
        knowledge="Test",
    )
    assert agent.trigger_pattern == "org/*"

    # Valid keyword agent
    agent = KnowledgeAgent(
        name="test",
        version="1.0.0",
        author="test",
        agent="CodeActAgent",
        category="testing",
        trigger_type=TriggerType.KEYWORD,
        triggers=["test"],
        description="Test",
        knowledge="Test",
    )
    assert agent.triggers == ["test"]


def test_template_agent_validation():
    """Test validation of template agents."""
    # Test input validation
    input1 = TemplateInput(
        name="test",
        description="Test input",
        type="string",
        required=True,
        validation=InputValidation(pattern=r"^test.*"),
    )
    assert input1.validation.pattern == r"^test.*"

    # Test template agent
    agent = TemplateAgent(
        name="test",
        version="1.0.0",
        author="test",
        agent="CodeActAgent",
        category="testing",
        template_type=TemplateType.WORKFLOW,
        description="Test",
        template="Test ${VAR}",
        inputs=[input1],
    )
    assert agent.template == "Test ${VAR}"
    assert len(agent.inputs) == 1


def test_microagent_hub_loading(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test loading of microagents from directory."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Check repository agents
    assert len(hub.repo_agents) == 1
    agent = hub.repo_agents["test_repo_agent"]
    assert agent.trigger_pattern == "test-org/*"
    assert agent.priority == 100

    # Check keyword agents
    assert len(hub.keyword_agents) == 1
    agent = hub.keyword_agents["test_keyword_agent"]
    assert "test" in agent.triggers
    assert "*.py" in agent.file_patterns

    # Check template agents
    assert len(hub.template_agents) == 1
    agent = hub.template_agents["test_template"]
    assert agent.template_type == TemplateType.WORKFLOW
    assert len(agent.inputs) == 2


def test_repo_agent_matching(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test matching of repository agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test matching repository
    agents = hub.get_repo_agents("test-org/repo1")
    assert len(agents) == 1
    assert agents[0].name == "test_repo_agent"

    # Test non-matching repository
    agents = hub.get_repo_agents("other-org/repo1")
    assert len(agents) == 0


def test_keyword_agent_matching(temp_microagents_dir, monkeypatch: MonkeyPatch):
    """Test matching of keyword agents."""
    # Patch required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test matching keyword
    agents = hub.get_keyword_agents("Running test with pytest")
    assert len(agents) == 1
    assert agents[0].name == "test_keyword_agent"

    # Test matching keyword with file pattern
    agents = hub.get_keyword_agents("Running test", "test.py")
    assert len(agents) == 1

    # Test matching keyword with non-matching file pattern
    agents = hub.get_keyword_agents("Running test", "test.txt")
    assert len(agents) == 0

    # Test non-matching keyword
    agents = hub.get_keyword_agents("No matches here")
    assert len(agents) == 0


def test_template_processing(temp_microagents_dir):
    """Test processing of templates."""
    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test with all variables
    result = hub.process_template(
        "test_template", {"VAR1": "value1", "VAR2": "value2"}
    )
    assert result == "Test value1 and value2"

    # Test with default value
    result = hub.process_template("test_template", {"VAR1": "value1"})
    assert result == "Test value1 and default"

    # Test missing required variable
    with pytest.raises(ValueError):
        hub.process_template("test_template", {"VAR2": "value2"})

    # Test non-existent template
    result = hub.process_template("non_existent", {})
    assert result is None


def test_template_listing(temp_microagents_dir):
    """Test listing of template agents."""
    hub = MicroAgentHub.load(temp_microagents_dir)

    # Test listing all templates
    templates = hub.list_template_agents()
    assert len(templates) == 1

    # Test listing by type
    templates = hub.list_template_agents(TemplateType.WORKFLOW)
    assert len(templates) == 1
    templates = hub.list_template_agents(TemplateType.SNIPPET)
    assert len(templates) == 0
