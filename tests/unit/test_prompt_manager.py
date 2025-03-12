import os
import shutil
import time
from unittest.mock import MagicMock

import pytest

from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import TextContent
from openhands.events.action.agent import AgentRecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource, RecallType
from openhands.events.observation.agent import MicroagentKnowledge, RecallObservation
from openhands.events.stream import EventStream
from openhands.memory.conversation_memory import ConversationMemory
from openhands.memory.memory import Memory
from openhands.microagent import (
    BaseMicroAgent,
)
from openhands.storage.memory import InMemoryFileStore
from openhands.utils.prompt import PromptManager, RepositoryInfo


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


def test_prompt_manager_template_rendering(prompt_dir):
    # Create temporary template files
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write("""System prompt: bar""")
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt: foo')
    with open(os.path.join(prompt_dir, 'additional_info.j2'), 'w') as f:
        f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to directory {{ repository_info.repo_directory }}.
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
    additional_info = manager.build_additional_info(
        repository_info=repo_info, runtime_info=None, repo_instructions=''
    )
    assert '<REPOSITORY_INFO>' in additional_info
    assert (
        "At the user's request, repository owner/repo has been cloned to directory /workspace/repo."
        in additional_info
    )
    assert '</REPOSITORY_INFO>' in additional_info
    assert manager.get_example_user_message() == 'User prompt: foo'

    # Clean up temporary files
    os.remove(os.path.join(prompt_dir, 'system_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'user_prompt.j2'))
    os.remove(os.path.join(prompt_dir, 'additional_info.j2'))


def test_prompt_manager_file_not_found(prompt_dir):
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
The following information has been included based on a keyword match for "{{ agent_info.trigger_word }}".
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


def test_memory_with_microagents(prompt_dir):
    """Test that Memory loads microagents and creates RecallObservations."""
    # Create a test microagent
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

    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory with the microagent directory
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )
    memory.microagents_dir = os.path.join(prompt_dir, 'micro')

    # Verify microagents were loaded
    assert len(memory.repo_microagents) == 0
    assert 'flarglebargle' in memory.knowledge_microagents

    # Create a recall action with the trigger word
    recall_action = AgentRecallAction(
        query='Hello, flarglebargle!', recall_type=RecallType.KNOWLEDGE_MICROAGENT
    )

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the recall action to the event stream
    event_stream.add_event(recall_action, EventSource.USER)

    # Clear the events list to only capture new events
    added_events.clear()

    # Process the recall action
    memory.on_event(recall_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.KNOWLEDGE_MICROAGENT
    assert len(observation.microagent_knowledge) == 1
    assert observation.microagent_knowledge[0].name == 'flarglebargle'
    assert observation.microagent_knowledge[0].trigger == 'flarglebargle'
    assert 'magic word' in observation.microagent_knowledge[0].content

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{microagent_name}.md'))


def test_memory_repository_info(prompt_dir):
    """Test that Memory adds repository info to RecallObservations."""
    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Initialize Memory
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )
    memory.microagents_dir = os.path.join(prompt_dir, 'micro')

    # Create a test repo microagent first
    repo_microagent_name = 'test_repo_microagent'
    repo_microagent_content = """---
name: test_repo
type: repo
agent: CodeActAgent
---

REPOSITORY INSTRUCTIONS: This is a test repository.
"""

    # Create a temporary repo microagent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent_content)

    # Reload microagents
    memory._load_global_microagents()

    # Set repository info
    memory.set_repository_info('owner/repo', '/workspace/repo')

    # Create and add the first user message
    user_message = MessageAction(content='First user message')
    user_message._source = EventSource.USER  # type: ignore[attr-defined]
    event_stream.add_event(user_message, EventSource.USER)

    # Create and add the recall action
    recall_action = AgentRecallAction(
        query='First user message', recall_type=RecallType.ENVIRONMENT_INFO
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]
    event_stream.add_event(recall_action, EventSource.USER)

    # Give it a little time to process
    time.sleep(0.3)

    # Get all events from the stream
    events = list(event_stream.get_events())

    # Find the RecallObservation event
    recall_obs_events = [
        event for event in events if isinstance(event, RecallObservation)
    ]

    # We should have at least one RecallObservation
    assert len(recall_obs_events) > 0

    # Get the first RecallObservation
    observation = recall_obs_events[0]
    assert observation.recall_type == RecallType.ENVIRONMENT_INFO
    assert observation.repo_name == 'owner/repo'
    assert observation.repo_directory == '/workspace/repo'
    assert 'This is a test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'))


def test_conversation_memory_processes_recall_observation(prompt_dir):
    """Test that ConversationMemory processes RecallObservations correctly."""
    # Create a microagent_info.j2 template file
    template_path = os.path.join(prompt_dir, 'microagent_info.j2')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("""{% for agent_info in triggered_agents %}
<EXTRA_INFO>
The following information has been included based on a keyword match for "{{ agent_info.trigger_word }}".
It may or may not be relevant to the user's request.

{{ agent_info.content }}
</EXTRA_INFO>
{% endfor %}
""")

    # Create a mock agent config
    agent_config = MagicMock(spec=AgentConfig)
    agent_config.enable_prompt_extensions = True
    agent_config.disabled_microagents = []

    # Create a PromptManager
    prompt_manager = PromptManager(prompt_dir=prompt_dir)

    # Initialize ConversationMemory
    conversation_memory = ConversationMemory(
        config=agent_config, prompt_manager=prompt_manager
    )

    # Create a RecallObservation with microagent knowledge
    recall_observation = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='test_agent',
                trigger='test_trigger',
                content='This is triggered content for testing.',
            )
        ],
        content='Recalled knowledge from microagents',
    )

    # Process the observation
    messages = conversation_memory._process_observation(
        obs=recall_observation,
        tool_call_id_to_message={},
        max_message_chars=None,
        current_index=0,
        events=[],
    )

    # Verify the message was created correctly
    assert len(messages) == 1
    message = messages[0]
    assert message.role == 'user'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    expected_text = """<EXTRA_INFO>
The following information has been included based on a keyword match for "test_trigger".
It may or may not be relevant to the user's request.

This is triggered content for testing.
</EXTRA_INFO>"""

    assert message.content[0].text.strip() == expected_text.strip()


def test_conversation_memory_processes_environment_info(prompt_dir):
    """Test that ConversationMemory processes environment info RecallObservations correctly."""
    # Create an additional_info.j2 template file
    template_path = os.path.join(prompt_dir, 'additional_info.j2')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
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

    # Create a mock agent config
    agent_config = MagicMock(spec=AgentConfig)
    agent_config.enable_prompt_extensions = True

    # Create a PromptManager
    prompt_manager = PromptManager(prompt_dir=prompt_dir)

    # Initialize ConversationMemory
    conversation_memory = ConversationMemory(
        config=agent_config, prompt_manager=prompt_manager
    )

    # Create a RecallObservation with environment info
    recall_observation = RecallObservation(
        recall_type=RecallType.ENVIRONMENT_INFO,
        repo_name='owner/repo',
        repo_directory='/workspace/repo',
        repo_instructions='This repository contains important code.',
        runtime_hosts={'example.com': 8080},
        additional_agent_instructions='You know everything about this runtime.',
        content='Recalled environment info',
    )

    # Process the observation
    messages = conversation_memory._process_observation(
        obs=recall_observation,
        tool_call_id_to_message={},
        max_message_chars=None,
        current_index=0,
        events=[],
    )

    # Verify the message was created correctly
    assert len(messages) == 1
    message = messages[0]
    assert message.role == 'user'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    # Check that the message contains the repository info
    assert '<REPOSITORY_INFO>' in message.content[0].text
    assert 'owner/repo' in message.content[0].text
    assert '/workspace/repo' in message.content[0].text

    # Check that the message contains the repository instructions
    assert '<REPOSITORY_INSTRUCTIONS>' in message.content[0].text
    assert 'This repository contains important code.' in message.content[0].text

    # Check that the message contains the runtime info
    assert '<RUNTIME_INFORMATION>' in message.content[0].text
    assert 'example.com (port 8080)' in message.content[0].text

    # Check that the message contains the additional agent instructions
    assert 'You know everything about this runtime.' in message.content[0].text
