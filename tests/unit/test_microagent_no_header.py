from pathlib import Path

from openhands.microagent.microagent import BaseMicroagent, RepoMicroagent
from openhands.microagent.types import MicroagentType


def test_load_markdown_without_frontmatter():
    """Test loading a markdown file without frontmatter."""
    content = '# Test Content\nThis is a test markdown file without frontmatter.'
    path = Path('test.md')

    # Load the agent from content using keyword argument
    agent = BaseMicroagent.load(path=path, file_content=content)

    # Verify it's loaded as a repo agent with default values
    assert isinstance(agent, RepoMicroagent)
    assert agent.name == 'default'
    assert agent.content == content
    assert agent.type == MicroagentType.REPO_KNOWLEDGE
    assert agent.metadata.agent == 'CodeActAgent'
    assert agent.metadata.version == '1.0.0'


def test_load_markdown_with_empty_frontmatter():
    """Test loading a markdown file with empty frontmatter."""
    content = (
        '---\n---\n# Test Content\nThis is a test markdown file with empty frontmatter.'
    )
    path = Path('test.md')

    # Load the agent from content using keyword argument
    agent = BaseMicroagent.load(path=path, file_content=content)

    # Verify it's loaded as a repo agent with default values
    assert isinstance(agent, RepoMicroagent)
    assert agent.name == 'default'
    assert (
        agent.content
        == '# Test Content\nThis is a test markdown file with empty frontmatter.'
    )
    assert agent.type == MicroagentType.REPO_KNOWLEDGE
    assert agent.metadata.agent == 'CodeActAgent'
    assert agent.metadata.version == '1.0.0'


def test_load_markdown_with_partial_frontmatter():
    """Test loading a markdown file with partial frontmatter."""
    content = """---
name: custom_name
---
# Test Content
This is a test markdown file with partial frontmatter."""
    path = Path('test.md')

    # Load the agent from content using keyword argument
    agent = BaseMicroagent.load(path=path, file_content=content)

    # Verify it uses provided name but default values for other fields
    assert isinstance(agent, RepoMicroagent)
    assert agent.name == 'custom_name'
    assert (
        agent.content
        == '# Test Content\nThis is a test markdown file with partial frontmatter.'
    )
    assert agent.type == MicroagentType.REPO_KNOWLEDGE
    assert agent.metadata.agent == 'CodeActAgent'
    assert agent.metadata.version == '1.0.0'


def test_load_markdown_with_full_frontmatter():
    """Test loading a markdown file with full frontmatter still works."""
    content = """---
name: test_agent
type: repo
agent: CustomAgent
version: 2.0.0
---
# Test Content
This is a test markdown file with full frontmatter."""
    path = Path('test.md')

    # Load the agent from content using keyword argument
    agent = BaseMicroagent.load(path=path, file_content=content)

    # Verify all provided values are used
    assert isinstance(agent, RepoMicroagent)
    assert agent.name == 'test_agent'
    assert (
        agent.content
        == '# Test Content\nThis is a test markdown file with full frontmatter.'
    )
    assert agent.type == MicroagentType.REPO_KNOWLEDGE
    assert agent.metadata.agent == 'CustomAgent'
    assert agent.metadata.version == '2.0.0'
