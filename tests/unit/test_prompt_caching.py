from unittest.mock import Mock

import pytest
from litellm import ModelResponse

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.action import MessageAction
from openhands.llm.llm import LLM


@pytest.fixture
def mock_llm():
    llm = LLM(
        LLMConfig(
            model='claude-3-5-sonnet-20241022',
            api_key='fake',
            caching_prompt=True,
        )
    )
    return llm


@pytest.fixture
def codeact_agent(mock_llm):
    config = AgentConfig()
    agent = CodeActAgent(mock_llm, config)
    return agent


def response_mock(content: str, tool_call_id: str):
    class MockModelResponse:
        def __init__(self, content, tool_call_id):
            self.choices = [
                {
                    'message': {
                        'content': content,
                        'tool_calls': [
                            {
                                'function': {
                                    'id': tool_call_id,
                                    'name': 'execute_bash',
                                    'arguments': '{}',
                                }
                            }
                        ],
                    }
                }
            ]

        def model_dump(self):
            return {'choices': self.choices}

    return ModelResponse(**MockModelResponse(content, tool_call_id).model_dump())


def test_get_messages(codeact_agent: CodeActAgent):
    # Add some events to history
    history = list()
    message_action_1 = MessageAction('Initial user message')
    message_action_1._source = 'user'
    history.append(message_action_1)
    message_action_2 = MessageAction('Sure!')
    message_action_2._source = 'assistant'
    history.append(message_action_2)
    message_action_3 = MessageAction('Hello, agent!')
    message_action_3._source = 'user'
    history.append(message_action_3)
    message_action_4 = MessageAction('Hello, user!')
    message_action_4._source = 'assistant'
    history.append(message_action_4)
    message_action_5 = MessageAction('Laaaaaaaast!')
    message_action_5._source = 'user'
    history.append(message_action_5)

    codeact_agent.reset()
    messages = codeact_agent._get_messages(
        Mock(history=history, max_iterations=5, iteration=0, extra_data={})
    )

    assert (
        len(messages) == 6
    )  # System, initial user + user message, agent message, last user message
    assert messages[0].content[0].cache_prompt  # system message
    assert messages[1].role == 'user'
    assert messages[1].content[0].text.endswith('Initial user message')
    # we add cache breakpoint to the last 3 user messages
    assert messages[1].content[0].cache_prompt

    assert messages[3].role == 'user'
    assert messages[3].content[0].text == ('Hello, agent!')
    assert messages[3].content[0].cache_prompt
    assert messages[4].role == 'assistant'
    assert messages[4].content[0].text == 'Hello, user!'
    assert not messages[4].content[0].cache_prompt
    assert messages[5].role == 'user'
    assert messages[5].content[0].text.startswith('Laaaaaaaast!')
    assert messages[5].content[0].cache_prompt


def test_get_messages_prompt_caching(codeact_agent: CodeActAgent):
    history = list()
    # Add multiple user and agent messages
    for i in range(15):
        message_action_user = MessageAction(f'User message {i}')
        message_action_user._source = 'user'
        history.append(message_action_user)
        message_action_agent = MessageAction(f'Agent message {i}')
        message_action_agent._source = 'assistant'
        history.append(message_action_agent)

    codeact_agent.reset()
    messages = codeact_agent._get_messages(
        Mock(history=history, max_iterations=10, iteration=5, extra_data={})
    )

    # Check that only the last two user messages have cache_prompt=True
    cached_user_messages = [
        msg
        for msg in messages
        if msg.role in ('user', 'system') and msg.content[0].cache_prompt
    ]
    assert (
        len(cached_user_messages) == 4
    )  # Including the initial system+user + 2 last user message

    # Verify that these are indeed the last two user messages (from start)
    assert cached_user_messages[0].content[0].text.startswith('You are OpenHands agent')
    assert cached_user_messages[2].content[0].text.startswith('User message 1')
    assert cached_user_messages[3].content[0].text.startswith('User message 1')


def test_prompt_caching_headers(codeact_agent: CodeActAgent):
    history = list()
    # Setup
    msg1 = MessageAction('Hello, agent!')
    msg1._source = 'user'
    history.append(msg1)
    msg2 = MessageAction('Hello, user!')
    msg2._source = 'agent'
    history.append(msg2)

    mock_state = Mock()
    mock_state.history = history
    mock_state.max_iterations = 5
    mock_state.iteration = 0
    mock_state.extra_data = {}

    codeact_agent.reset()

    # Create a mock for litellm_completion
    def check_headers(**kwargs):
        assert 'extra_headers' in kwargs
        assert 'anthropic-beta' in kwargs['extra_headers']
        assert kwargs['extra_headers']['anthropic-beta'] == 'prompt-caching-2024-07-31'
        return ModelResponse(
            choices=[{'message': {'content': 'Hello! How can I assist you today?'}}]
        )

    codeact_agent.llm._completion_unwrapped = check_headers
    result = codeact_agent.step(mock_state)

    # Assert
    assert isinstance(result, MessageAction)
    assert result.content == 'Hello! How can I assist you today?'
