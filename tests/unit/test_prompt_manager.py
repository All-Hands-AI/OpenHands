import os
import shutil

import pytest

from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.events.observation.agent import MicroagentKnowledge
from openhands.microagent import BaseMicroAgent
from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


def test_prompt_manager_template_rendering(prompt_dir):
    """Test PromptManager's template rendering functionality."""
    # Create temporary template files
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write("""System prompt: bar""")
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt: foo')
    with open(os.path.join(prompt_dir, 'additional_info.j2'), 'w') as f:
        f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to the current working directory {{ repository_info.repo_directory }}.
</REPOSITORY_INFO>
{% endif %}
""")

    # Test without GitHub repo
    manager = PromptManager(prompt_dir)
    assert manager.get_system_message() == 'System prompt: bar'
    assert manager.get_example_user_message() == 'User prompt: foo'

    # Test with GitHub repo
    manager = PromptManager(prompt_dir=prompt_dir)
    repo_info = RepositoryInfo(repo_name='owner/repo', repo_directory='/workspace/repo')

    # verify its parts are rendered
    system_msg = manager.get_system_message()
    assert 'System prompt: bar' in system_msg

    # Test building additional info
    additional_info = manager.build_workspace_context(
        repository_info=repo_info, runtime_info=None, repo_instructions=''
    )
    assert '<REPOSITORY_INFO>' in additional_info
    assert (
        "At the user's request, repository owner/repo has been cloned to the current working directory /workspace/repo."
        in additional_info
    )
    assert '</REPOSITORY_INFO>' in additional_info
    assert manager.get_example_user_message() == 'User prompt: foo'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'additional_info.j2'))


def test_prompt_manager_file_not_found(prompt_dir):
    """Test PromptManager behavior when a template file is not found."""
    # Test with a non-existent template
    with pytest.raises(FileNotFoundError):
        BaseMicroAgent.load(
            os.path.join(prompt_dir, 'micro', 'non_existent_microagent.md')
        )


def test_build_microagent_info(prompt_dir):
    """Test the build_microagent_info method with the microagent_info.j2 template."""
    # Prepare a microagent_info.j2 template file if it doesn't exist
    template_path = os.path.join(prompt_dir, 'microagent_info.j2')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("""{% for agent_info in triggered_agents %}
<EXTRA_INFO>
The following information has been included based on a keyword match for "{{ agent_info.trigger }}".
It may or may not be relevant to the user's request.

{{ agent_info.content }}
</EXTRA_INFO>
{% endfor %}
""")

    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Test with a single triggered agent
    triggered_agents = [
        MicroagentKnowledge(
            name='test_agent1',
            trigger='keyword1',
            content='This is information from agent 1',
        )
    ]
    result = manager.build_microagent_info(triggered_agents)
    expected = """<EXTRA_INFO>
The following information has been included based on a keyword match for "keyword1".
It may or may not be relevant to the user's request.

This is information from agent 1
</EXTRA_INFO>"""
    assert result.strip() == expected.strip()

    # Test with multiple triggered agents
    triggered_agents = [
        MicroagentKnowledge(
            name='test_agent1',
            trigger='keyword1',
            content='This is information from agent 1',
        ),
        MicroagentKnowledge(
            name='test_agent2',
            trigger='keyword2',
            content='This is information from agent 2',
        ),
    ]
    result = manager.build_microagent_info(triggered_agents)
    expected = """<EXTRA_INFO>
The following information has been included based on a keyword match for "keyword1".
It may or may not be relevant to the user's request.

This is information from agent 1
</EXTRA_INFO>

<EXTRA_INFO>
The following information has been included based on a keyword match for "keyword2".
It may or may not be relevant to the user's request.

This is information from agent 2
</EXTRA_INFO>"""
    assert result.strip() == expected.strip()

    # Test with no triggered agents
    result = manager.build_microagent_info([])
    assert result.strip() == ''


def test_add_examples_to_initial_message(prompt_dir):
    """Test adding example messages to an initial message."""
    # Create a user_prompt.j2 template file
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('This is an example user message')

    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Create a message
    message = Message(role='user', content=[TextContent(text='Original content')])

    # Add examples to the message
    manager.add_examples_to_initial_message(message)

    # Check that the example was added at the beginning
    assert len(message.content) == 2
    assert message.content[0].text == 'This is an example user message'
    assert message.content[1].text == 'Original content'

    # Clean up
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))


def test_add_turns_left_reminder(prompt_dir):
    """Test adding turns left reminder to messages."""
    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Create a State object with specific iteration values
    state = State()
    state.iteration = 3
    state.max_iterations = 10

    # Create a list of messages with a user message
    user_message = Message(role='user', content=[TextContent(text='User content')])
    assistant_message = Message(
        role='assistant', content=[TextContent(text='Assistant content')]
    )
    messages = [assistant_message, user_message]

    # Add turns left reminder
    manager.add_turns_left_reminder(messages, state)

    # Check that the reminder was added to the latest user message
    assert len(user_message.content) == 2
    assert (
        'ENVIRONMENT REMINDER: You have 7 turns left to complete the task.'
        in user_message.content[1].text
    )


def test_build_workspace_context_with_repo_and_runtime(prompt_dir):
    """Test building additional info with repository and runtime information."""
    # Create an additional_info.j2 template file
    with open(os.path.join(prompt_dir, 'additional_info.j2'), 'w') as f:
        f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to directory {{ repository_info.repo_directory }}.
</REPOSITORY_INFO>
{% endif %}

{% if repository_instructions %}
<REPOSITORY_INSTRUCTIONS>
{{ repository_instructions }}
</REPOSITORY_INSTRUCTIONS>
{% endif %}

{% if runtime_info and (runtime_info.available_hosts or runtime_info.additional_agent_instructions) -%}
<RUNTIME_INFORMATION>
{% if runtime_info.available_hosts %}
The user has access to the following hosts for accessing a web application,
each of which has a corresponding port:
{% for host, port in runtime_info.available_hosts.items() %}
* {{ host }} (port {{ port }})
{% endfor %}
{% endif %}

{% if runtime_info.additional_agent_instructions %}
{{ runtime_info.additional_agent_instructions }}
{% endif %}
</RUNTIME_INFORMATION>
{% endif %}
""")

    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Create repository and runtime information
    repo_info = RepositoryInfo(repo_name='owner/repo', repo_directory='/workspace/repo')
    runtime_info = RuntimeInfo(
        available_hosts={'example.com': 8080},
        additional_agent_instructions='You know everything about this runtime.',
    )
    repo_instructions = 'This repository contains important code.'

    # Build additional info
    result = manager.build_workspace_context(
        repository_info=repo_info,
        runtime_info=runtime_info,
        repo_instructions=repo_instructions,
    )

    # Check that all information is included
    assert '<REPOSITORY_INFO>' in result
    assert 'owner/repo' in result
    assert '/workspace/repo' in result
    assert '<REPOSITORY_INSTRUCTIONS>' in result
    assert 'This repository contains important code.' in result
    assert '<RUNTIME_INFORMATION>' in result
    assert 'example.com (port 8080)' in result
    assert 'You know everything about this runtime.' in result

    # Clean up
    os.remove(os.path.join(prompt_dir, 'additional_info.j2'))


def test_prompt_manager_initialization_error():
    """Test that PromptManager raises an error if the prompt directory is not set."""
    with pytest.raises(ValueError, match='Prompt directory is not set'):
        PromptManager(None)
