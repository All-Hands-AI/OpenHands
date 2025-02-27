from unittest.mock import MagicMock

import pytest

from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.events.action import MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


@pytest.fixture
def conversation_memory():
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    return ConversationMemory(prompt_manager)


@pytest.fixture
def mock_state():
    state = MagicMock(spec=State)
    state.history = []
    return state


def test_process_initial_messages(conversation_memory):
    messages = conversation_memory.process_initial_messages(with_caching=False)
    assert len(messages) == 1
    assert messages[0].role == 'system'
    assert messages[0].content[0].text == 'System message'
    assert messages[0].content[0].cache_prompt is False

    messages = conversation_memory.process_initial_messages(with_caching=True)
    assert messages[0].content[0].cache_prompt is True


def test_process_events_with_message_action(conversation_memory, mock_state):
    user_message = MessageAction(content='Hello', source='user')
    assistant_message = MessageAction(content='Hi there', source='assistant')

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        state=mock_state,
        condensed_history=[user_message, assistant_message],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 3
    assert messages[0].role == 'system'
    assert messages[1].role == 'user'
    assert messages[1].content[0].text == 'Hello'
    assert messages[2].role == 'assistant'
    assert messages[2].content[0].text == 'Hi there'


def test_process_events_with_observation(conversation_memory, mock_state):
    user_message = MessageAction(content='Hello', source='user')
    cmd_output = CmdOutputObservation(
        command='ls',
        exit_code=0,
        output='file1.txt\nfile2.txt',
        tool_call_metadata=None,
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        state=mock_state,
        condensed_history=[user_message, cmd_output],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 3
    assert messages[0].role == 'system'
    assert messages[1].role == 'user'
    assert messages[2].role == 'user'
    assert 'Observed result of command executed by user' in messages[2].content[0].text
    assert 'file1.txt' in messages[2].content[0].text


def test_apply_prompt_caching(conversation_memory):
    messages = [
        Message(role='system', content=[TextContent(text='System message')]),
        Message(role='user', content=[TextContent(text='User message')]),
        Message(role='assistant', content=[TextContent(text='Assistant message')]),
        Message(role='user', content=[TextContent(text='Another user message')]),
    ]

    conversation_memory.apply_prompt_caching(messages)

    # Only the last user message should have cache_prompt=True
    assert messages[0].content[0].cache_prompt is False
    assert messages[1].content[0].cache_prompt is False
    assert messages[2].content[0].cache_prompt is False
    assert messages[3].content[0].cache_prompt is True
