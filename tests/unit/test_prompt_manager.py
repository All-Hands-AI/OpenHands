import os
import shutil
from unittest.mock import Mock

import pytest

from openhands.utils.microagent import MicroAgent
from openhands.utils.prompt import PromptManager


@pytest.fixture
def prompt_dir(tmp_path):
    """Creates a temporary directory with CodeAct agent templates.

    Copies the entire codeact_agent directory structure to a temp location
    to avoid modifying the original files during tests.
    """
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    source = 'openhands/agenthub/codeact_agent'
    shutil.copytree(source, tmp_path, dirs_exist_ok=True)

    # Return path to the prompts directory
    return str(
        os.path.join(tmp_path, 'prompts')
    )  # Points to the correct prompts directory


SAMPLE_AGENT_SKILLS_DOCS = """Sample agent skills documentation"""


@pytest.fixture
def agent_skills_docs():
    return SAMPLE_AGENT_SKILLS_DOCS


def test_prompt_manager_without_micro_agent(prompt_dir, agent_skills_docs):
    manager = PromptManager(prompt_dir)

    assert manager.prompt_dir == prompt_dir
    # assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent is None

    assert isinstance(manager.system_message, str)
    assert (
        "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed answers to the user's questions."
        in manager.system_message
    )
    # assert SAMPLE_AGENT_SKILLS_DOCS in manager.system_message
    assert isinstance(manager.initial_user_message, str)
    assert '--- BEGIN OF GUIDELINE ---' not in manager.initial_user_message
    assert '--- END OF GUIDELINE ---' not in manager.initial_user_message
    assert "NOW, LET'S START!" in manager.initial_user_message
    assert 'micro_agent' not in manager.initial_user_message


def test_prompt_manager_with_micro_agent(prompt_dir, agent_skills_docs):
    micro_agent_name = 'test_micro_agent'
    micro_agent_content = (
        '## Micro Agent\n'
        'This is a test micro agent.\n'
        'It is used to test the prompt manager.\n'
    )

    # Create a temporary micro agent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(os.path.join(prompt_dir, 'micro', f'{micro_agent_name}.md'), 'w') as f:
        f.write(micro_agent_content)

    # Mock MicroAgent
    mock_micro_agent = Mock(spec=MicroAgent)
    mock_micro_agent.content = micro_agent_content

    manager = PromptManager(
        prompt_dir=prompt_dir,
        micro_agent=mock_micro_agent,
    )

    assert manager.prompt_dir == prompt_dir
    # assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent == mock_micro_agent

    assert isinstance(manager.system_message, str)
    assert (
        "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed answers to the user's questions."
        in manager.system_message
    )
    # assert SAMPLE_AGENT_SKILLS_DOCS in manager.system_message

    assert isinstance(manager.initial_user_message, str)
    assert (
        '--- BEGIN OF GUIDELINE ---\n'
        + 'The following information may assist you in completing your task:\n\n'
        + micro_agent_content
        + '\n'
        + '--- END OF GUIDELINE ---\n'
        + "\n\nNOW, LET'S START!"
    ) in manager.initial_user_message
    assert micro_agent_content in manager.initial_user_message

    # Clean up the temporary file
    os.remove(os.path.join(prompt_dir, 'micro', f'{micro_agent_name}.md'))


def test_prompt_manager_file_not_found(prompt_dir, agent_skills_docs):
    with pytest.raises(FileNotFoundError):
        MicroAgent(os.path.join(prompt_dir, 'micro', 'non_existent_micro_agent.md'))


def test_prompt_manager_template_rendering(prompt_dir, agent_skills_docs):
    # Create temporary template files
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write('System prompt: {{ agent_skills_docs }}')
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt: {{ micro_agent }}')

    manager = PromptManager(prompt_dir)

    # assert manager.system_message == f'System prompt: {agent_skills_docs}'
    assert manager.initial_user_message == 'User prompt: None'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))


def test_prompt_manager_loads_agent_skill(prompt_dir):
    manager = PromptManager(prompt_dir)
    assert (
        'open_file(path: str, line_number: int | None = 1, context_lines: int | None = 100) -> None'
        in manager.system_message
    )


def test_prompt_manager_block_rendering(prompt_dir):
    """Test that blocks are rendered correctly from templates."""
    manager = PromptManager(prompt_dir)

    # System blocks should contain core capabilities
    system_msg = manager.system_message
    assert (
        'A chat between a curious user and an artificial intelligence assistant'
        in system_msg
    )  # system_prefix block
    assert '<execute_ipython>' in system_msg  # python_capabilities block
    assert '<execute_bash>' in system_msg  # bash_capabilities block
    assert 'browse the Internet' in system_msg  # browsing_capabilities block
    assert '%pip install' in system_msg  # pip_capabilities block


def test_prompt_manager_agent_skills_blocks(prompt_dir):
    """Test that agent skills blocks are rendered with proper docstrings.
    This ensures skills documentation is correctly loaded and formatted."""
    manager = PromptManager(prompt_dir)

    # Check if specific skill docstrings are present
    skills_content = manager._render_blocks(
        'agent_skills', available_skills=['file_ops:open_file']
    )

    # Should contain function signature and docstring
    assert 'open_file(path: str' in skills_content
    assert 'Opens and displays the content of a file' in skills_content


def test_prompt_manager_micro_agent_blocks(prompt_dir):
    """Test micro-agent block rendering with and without micro-agent content.
    Verifies conditional rendering of micro-agent guidelines."""
    # Test without micro-agent
    manager = PromptManager(prompt_dir)
    micro_content = manager._render_blocks('micro_agent')
    assert '--- BEGIN OF GUIDELINE ---' not in micro_content

    # Test with micro-agent
    mock_micro_agent = Mock(spec=MicroAgent)
    mock_micro_agent.content = 'Test micro-agent content'
    manager = PromptManager(prompt_dir, micro_agent=mock_micro_agent)

    micro_content = manager._render_blocks(
        'micro_agent', micro_agent=mock_micro_agent.content
    )
    assert '--- BEGIN OF GUIDELINE ---' in micro_content
    assert 'Test micro-agent content' in micro_content


def test_prompt_manager_custom_block_order(prompt_dir):
    """Test that blocks are rendered in the order specified"""
    # Create a custom agent.yaml with specific block order
    custom_yaml = """
template:
  system_prompt:
    file: "system_prompt"
    blocks:
      - system_prefix
      - python_capabilities
      - agent_skills
    """

    yaml_path = os.path.join(prompt_dir, 'agent.yaml')
    with open(yaml_path, 'w') as f:
        f.write(custom_yaml)

    manager = PromptManager(prompt_dir)
    system_msg = manager.system_message

    # Verify block order
    prefix_pos = system_msg.find('You are a new generation AI assistant')
    python_pos = system_msg.find('<execute_ipython>')
    skills_pos = system_msg.find('open_file(path: str')

    # Blocks should appear in specified order
    assert prefix_pos < python_pos < skills_pos
    assert '<execute_bash>' not in system_msg  # This block wasn't included


def test_prompt_manager_missing_blocks(prompt_dir):
    """Test graceful handling of missing or undefined blocks.
    Ensures the system doesn't crash on template/block misconfigurations."""
    # Create yaml with non-existent block
    custom_yaml = """
template:
  system_prompt:
    file: "system_prompt"
    blocks:
      - nonexistent_block
    """

    yaml_path = os.path.join(prompt_dir, 'agent.yaml')
    with open(yaml_path, 'w') as f:
        f.write(custom_yaml)

    # Should not raise exception, but log warning and skip block
    manager = PromptManager(prompt_dir)
    assert manager.system_message.strip() != ''


def test_prompt_manager_block_inheritance(prompt_dir):
    """Test that blocks can be overridden in custom templates.
    Verifies template inheritance and customization capabilities."""
    # Create custom templates directory
    custom_dir = os.path.join(prompt_dir, 'user_templates')
    os.makedirs(custom_dir, exist_ok=True)

    # Create custom system template that overrides a block
    custom_template = """
{% block system_prefix %}
Custom system prefix override
{% endblock %}
    """

    with open(os.path.join(custom_dir, 'system_prompt.j2'), 'w') as f:
        f.write(custom_template)

    manager = PromptManager(prompt_dir)
    assert 'Custom system prefix override' in manager.system_message


def test_prompt_manager_default_templates(prompt_dir):
    """Test that default templates are loaded correctly when no yaml exists.
    Verifies the fallback configuration works as expected."""
    # Remove agent.yaml to force default template loading
    yaml_path = os.path.join(prompt_dir, 'agent.yaml')
    if os.path.exists(yaml_path):
        os.remove(yaml_path)

    manager = PromptManager(prompt_dir)
    templates = manager.templates

    # Check structure matches expected defaults
    assert 'system_prompt' in templates
    assert 'agent_skills' in templates
    assert 'examples' in templates
    assert 'micro_agent' in templates
    assert 'user_prompt' in templates

    # Verify default block configuration
    system_blocks = templates['system_prompt']['blocks']
    assert 'system_prefix' in system_blocks
    assert 'python_capabilities' in system_blocks
    assert 'bash_capabilities' in system_blocks

    # Verify templates are loaded and functional
    assert isinstance(manager.system_message, str)
    assert isinstance(manager.initial_user_message, str)


def test_prompt_manager_agent_skills_block_name(prompt_dir):
    """Verify that agent_skills template has the correct block name."""
    manager = PromptManager(prompt_dir)
    template_info = manager.templates['agent_skills']
    assert 'skill_docs' in template_info['blocks']
