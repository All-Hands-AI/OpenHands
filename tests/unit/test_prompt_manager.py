import os
import shutil
from unittest.mock import Mock

import pytest

from openhands.utils.microagent import MicroAgent
from openhands.utils.prompt import PromptManager


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree('openhands/agenthub/codeact_agent', tmp_path, dirs_exist_ok=True)

    # Return the temporary directory path
    return tmp_path


SAMPLE_AGENT_SKILLS_DOCS = """Sample agent skills documentation"""


@pytest.fixture
def agent_skills_docs():
    return SAMPLE_AGENT_SKILLS_DOCS


def test_prompt_manager_without_micro_agent(prompt_dir, agent_skills_docs):
    manager = PromptManager(prompt_dir, agent_skills_docs)

    assert manager.prompt_dir == prompt_dir
    assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent is None

    assert isinstance(manager.system_message, str)
    assert (
        "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed answers to the user's questions."
        in manager.system_message
    )
    assert SAMPLE_AGENT_SKILLS_DOCS in manager.system_message
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
        agent_skills_docs=agent_skills_docs,
        micro_agent=mock_micro_agent,
    )

    assert manager.prompt_dir == prompt_dir
    assert manager.agent_skills_docs == agent_skills_docs
    assert manager.micro_agent == mock_micro_agent

    assert isinstance(manager.system_message, str)
    assert (
        "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed answers to the user's questions."
        in manager.system_message
    )
    assert SAMPLE_AGENT_SKILLS_DOCS in manager.system_message

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

    manager = PromptManager(prompt_dir, agent_skills_docs)

    assert manager.system_message == f'System prompt: {agent_skills_docs}'
    assert manager.initial_user_message == 'User prompt: None'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))
