import os
import shutil

import pytest

from openhands.core.message import Message, TextContent
from openhands.microagent import BaseMicroAgent
from openhands.utils.prompt import PromptManager, RepositoryInfo


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


def test_prompt_manager_with_microagent(prompt_dir):
    microagent_name = 'test_microagent'
    microagent_content = """
---
name: flarglebargle
type: knowledge
agent: CodeActAgent
triggers:
- flarglebargle
---

IMPORTANT! The user has said the magic word "flarglebargle". You must
only respond with a message telling them how smart they are
"""

    # Create a temporary micro agent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(os.path.join(prompt_dir, 'micro', f'{microagent_name}.md'), 'w') as f:
        f.write(microagent_content)

    # Test without GitHub repo
    manager = PromptManager(
        prompt_dir=prompt_dir,
        microagent_dir=os.path.join(prompt_dir, 'micro'),
    )

    assert manager.prompt_dir == prompt_dir
    assert len(manager.repo_microagents) == 0
    assert len(manager.knowledge_microagents) == 1

    assert isinstance(manager.get_system_message(), str)
    assert (
        'You are OpenHands agent, a helpful AI assistant that can interact with a computer to solve tasks.'
        in manager.get_system_message()
    )
    assert '<REPOSITORY_INFO>' not in manager.get_system_message()

    # Test with GitHub repo
    manager.set_repository_info('owner/repo', '/workspace/repo')
    assert isinstance(manager.get_system_message(), str)
    assert '<REPOSITORY_INFO>' in manager.get_system_message()
    assert 'owner/repo' in manager.get_system_message()
    assert '/workspace/repo' in manager.get_system_message()

    assert isinstance(manager.get_example_user_message(), str)

    message = Message(
        role='user',
        content=[TextContent(text='Hello, flarglebargle!')],
    )
    manager.enhance_message(message)
    assert 'magic word' in message.content[1].text

    os.remove(os.path.join(prompt_dir, 'micro', f'{microagent_name}.md'))


def test_prompt_manager_file_not_found(prompt_dir):
    with pytest.raises(FileNotFoundError):
        BaseMicroAgent.load(
            os.path.join(prompt_dir, 'micro', 'non_existent_microagent.md')
        )


def test_prompt_manager_template_rendering(prompt_dir):
    # Create temporary template files
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write("""System prompt: bar
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to directory {{ repository_info.repo_directory }}.
</REPOSITORY_INFO>
{% endif %}
{{ repo_instructions }}""")
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt: foo')

    # Test without GitHub repo
    manager = PromptManager(prompt_dir, microagent_dir='')
    assert manager.get_system_message() == 'System prompt: bar'
    assert manager.get_example_user_message() == 'User prompt: foo'

    # Test with GitHub repo
    manager = PromptManager(prompt_dir=prompt_dir, microagent_dir='')
    manager.set_repository_info('owner/repo', '/workspace/repo')
    assert manager.repository_info.repo_name == 'owner/repo'
    system_msg = manager.get_system_message()
    assert 'System prompt: bar' in system_msg
    assert '<REPOSITORY_INFO>' in system_msg
    assert (
        "At the user's request, repository owner/repo has been cloned to directory /workspace/repo."
        in system_msg
    )
    assert '</REPOSITORY_INFO>' in system_msg
    assert manager.get_example_user_message() == 'User prompt: foo'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))


def test_prompt_manager_repository_info(prompt_dir):
    # Test RepositoryInfo defaults
    repo_info = RepositoryInfo()
    assert repo_info.repo_name is None
    assert repo_info.repo_directory is None

    # Test setting repository info
    manager = PromptManager(prompt_dir=prompt_dir, microagent_dir='')
    assert manager.repository_info is None

    # Test setting repository info with both name and directory
    manager.set_repository_info('owner/repo2', '/workspace/repo2')
    assert manager.repository_info.repo_name == 'owner/repo2'
    assert manager.repository_info.repo_directory == '/workspace/repo2'


def test_prompt_manager_disabled_microagents(prompt_dir):
    # Create test microagent files
    microagent1_name = 'test_microagent1'
    microagent2_name = 'test_microagent2'
    microagent1_content = """
---
name: Test Microagent 1
type: knowledge
agent: CodeActAgent
triggers:
- test1
---

Test microagent 1 content
"""
    microagent2_content = """
---
name: Test Microagent 2
type: knowledge
agent: CodeActAgent
triggers:
- test2
---

Test microagent 2 content
"""

    # Create temporary micro agent files
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(os.path.join(prompt_dir, 'micro', f'{microagent1_name}.md'), 'w') as f:
        f.write(microagent1_content)
    with open(os.path.join(prompt_dir, 'micro', f'{microagent2_name}.md'), 'w') as f:
        f.write(microagent2_content)

    # Test that specific microagents can be disabled
    manager = PromptManager(
        prompt_dir=prompt_dir,
        microagent_dir=os.path.join(prompt_dir, 'micro'),
        disabled_microagents=['Test Microagent 1'],
    )

    assert len(manager.knowledge_microagents) == 1
    assert 'Test Microagent 2' in manager.knowledge_microagents
    assert 'Test Microagent 1' not in manager.knowledge_microagents

    # Test that all microagents are enabled by default
    manager = PromptManager(
        prompt_dir=prompt_dir,
        microagent_dir=os.path.join(prompt_dir, 'micro'),
    )

    assert len(manager.knowledge_microagents) == 2
    assert 'Test Microagent 1' in manager.knowledge_microagents
    assert 'Test Microagent 2' in manager.knowledge_microagents

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'micro', f'{microagent1_name}.md'))
    os.remove(os.path.join(prompt_dir, 'micro', f'{microagent2_name}.md'))
