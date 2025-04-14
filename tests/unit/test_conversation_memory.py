from unittest.mock import MagicMock

import pytest

from openhands.core.config.agent_config import AgentConfig
from openhands.events.action.message import MessageAction, SystemMessageAction
from openhands.events.event import EventSource
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


@pytest.fixture
def agent_config():
    return AgentConfig(
        enable_prompt_extensions=True,
        enable_som_visual_browsing=True,
    )


@pytest.fixture
def conversation_memory(agent_config):
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    prompt_manager.build_workspace_context.return_value = (
        'Formatted repository and runtime info'
    )
    return ConversationMemory(agent_config, prompt_manager)


def test_system_message_in_events(conversation_memory):
    """Test that SystemMessageAction in condensed_history is processed correctly."""
    # Create a system message action
    system_message = SystemMessageAction(content='System message', tools=['test_tool'])
    system_message._source = EventSource.AGENT

    # Process events with the system message in condensed_history
    messages = conversation_memory.process_events(
        condensed_history=[system_message],
        max_message_chars=None,
        vision_is_active=False,
    )

    # Check that the system message was processed correctly
    assert len(messages) == 1
    assert messages[0].role == 'system'
    assert messages[0].content[0].text == 'System message'


def test_process_events_with_message_action(conversation_memory):
    """Test that MessageAction is processed correctly."""
    # Create a system message action
    system_message = SystemMessageAction(content='System message')
    system_message._source = EventSource.AGENT

    # Create user and assistant messages
    user_message = MessageAction(content='Hello')
    user_message._source = EventSource.USER
    assistant_message = MessageAction(content='Hi there')
    assistant_message._source = EventSource.AGENT

    # Process events
    messages = conversation_memory.process_events(
        condensed_history=[system_message, user_message, assistant_message],
        max_message_chars=None,
        vision_is_active=False,
    )

    # Check that the messages were processed correctly
    assert len(messages) == 3
    assert messages[0].role == 'system'
    assert messages[0].content[0].text == 'System message'
    assert messages[1].role == 'user'
    assert messages[1].content[0].text == 'Hello'
    assert messages[2].role == 'assistant'
    assert messages[2].content[0].text == 'Hi there'
