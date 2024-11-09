from unittest.mock import Mock, patch

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.llm.llm import LLM


@pytest.fixture
def mock_llm():
    llm = Mock(spec=LLM)
    llm.config = LLMConfig(model='claude-3-5-sonnet-20241022', caching_prompt=True)
    llm.is_caching_prompt_active.return_value = True
    return llm


@pytest.fixture(params=[False, True])
def codeact_agent(mock_llm, request):
    config = AgentConfig()
    config.function_calling = request.param
    return CodeActAgent(mock_llm, config)


def response_mock(content: str):
    class MockModelResponse:
        def __init__(self, content):
            self.choices = [
                {
                    'message': {
                        'content': content,
                        'tool_calls': [
                            {
                                'function': {
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

    return MockModelResponse(content)


def test_get_messages_with_reminder(codeact_agent: CodeActAgent):
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
        Mock(history=history, max_iterations=5, iteration=0)
    )

    assert (
        len(messages) == 6
    )  # System, initial user + user message, agent message, last user message
    assert messages[0].content[0].cache_prompt  # system message
    assert messages[1].role == 'user'
    if not codeact_agent.config.function_calling:
        assert messages[1].content[0].text.endswith("LET'S START!")
        assert messages[1].content[1].text.endswith('Initial user message')
    else:
        assert messages[1].content[0].text.endswith('Initial user message')
    # we add cache breakpoint to the last 3 user messages
    assert messages[1].content[-1].cache_prompt

    assert messages[3].role == 'user'
    assert messages[3].content[0].text == ('Hello, agent!')
    assert messages[3].content[0].cache_prompt
    assert messages[4].role == 'assistant'
    assert messages[4].content[0].text == 'Hello, user!'
    assert not messages[4].content[0].cache_prompt
    assert messages[5].role == 'user'
    assert messages[5].content[0].text.startswith('Laaaaaaaast!')
    assert messages[5].content[0].cache_prompt
    if not codeact_agent.config.function_calling:
        assert (
            messages[5]
            .content[1]
            .text.endswith(
                'ENVIRONMENT REMINDER: You have 5 turns left to complete the task. When finished reply with <finish></finish>.'
            )
        )


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
        Mock(history=history, max_iterations=10, iteration=5)
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
    if not codeact_agent.config.function_calling:
        assert (
            cached_user_messages[0].content[0].text.startswith('A chat between')
        )  # system message
    assert cached_user_messages[2].content[0].text.startswith('User message 1')
    assert cached_user_messages[3].content[0].text.startswith('User message 1')


def test_get_messages_with_cmd_action(codeact_agent: CodeActAgent):
    if codeact_agent.config.function_calling:
        pytest.skip('Skipping this test for function calling')

    history = list()

    # Add a mix of actions and observations
    message_action_1 = MessageAction(
        "Let's list the contents of the current directory."
    )
    message_action_1._source = 'user'
    history.append(message_action_1)

    cmd_action_1 = CmdRunAction('ls -l', thought='List files in current directory')
    cmd_action_1._source = 'agent'
    cmd_action_1._id = 'cmd_1'
    history.append(cmd_action_1)

    cmd_observation_1 = CmdOutputObservation(
        content='total 0\n-rw-r--r-- 1 user group 0 Jan 1 00:00 file1.txt\n-rw-r--r-- 1 user group 0 Jan 1 00:00 file2.txt',
        command_id=cmd_action_1._id,
        command='ls -l',
        exit_code=0,
    )
    cmd_observation_1._source = 'user'
    history.append(cmd_observation_1)

    message_action_2 = MessageAction("Now, let's create a new directory.")
    message_action_2._source = 'agent'
    history.append(message_action_2)

    cmd_action_2 = CmdRunAction('mkdir new_directory', thought='Create a new directory')
    cmd_action_2._source = 'agent'
    cmd_action_2._id = 'cmd_2'
    history.append(cmd_action_2)

    cmd_observation_2 = CmdOutputObservation(
        content='',
        command_id=cmd_action_2._id,
        command='mkdir new_directory',
        exit_code=0,
    )
    cmd_observation_2._source = 'user'
    history.append(cmd_observation_2)

    codeact_agent.reset()
    messages = codeact_agent._get_messages(
        Mock(history=history, max_iterations=5, iteration=0)
    )

    # Assert the presence of key elements in the messages
    assert (
        messages[1]
        .content[-1]
        .text.startswith("Let's list the contents of the current directory.")
    )  # user, included in the initial message
    if not codeact_agent.config.function_calling:
        assert any(
            'List files in current directory\n<execute_bash>\nls -l\n</execute_bash>'
            in msg.content[0].text
            for msg in messages
        )  # agent
    assert any(
        'total 0\n-rw-r--r-- 1 user group 0 Jan 1 00:00 file1.txt\n-rw-r--r-- 1 user group 0 Jan 1 00:00 file2.txt'
        in msg.content[0].text
        for msg in messages
    )  # user, observation
    assert any(
        "Now, let's create a new directory." in msg.content[0].text for msg in messages
    )  # agent
    if not codeact_agent.config.function_calling:
        assert messages[4].content[1].text.startswith('Create a new directory')  # agent
    assert any(
        'finished with exit code 0' in msg.content[0].text for msg in messages
    )  # user, observation
    assert (
        messages[5].content[0].text.startswith('OBSERVATION:\n\n')
    )  # user, observation

    # prompt cache is added to the system message
    assert messages[0].content[0].cache_prompt
    # and the first initial user message
    assert messages[1].content[-1].cache_prompt
    # and to the last two user messages
    assert messages[3].content[0].cache_prompt
    assert messages[5].content[0].cache_prompt

    # reminder is added to the last user message
    if not codeact_agent.config.function_calling:
        assert 'ENVIRONMENT REMINDER: You have 5 turns' in messages[5].content[1].text


def test_prompt_caching_headers(codeact_agent: CodeActAgent):
    history = list()
    if codeact_agent.config.function_calling:
        pytest.skip('Skipping this test for function calling')

    # Setup
    history.append(MessageAction('Hello, agent!'))
    history.append(MessageAction('Hello, user!'))

    mock_state = Mock()
    mock_state.history = history
    mock_state.max_iterations = 5
    mock_state.iteration = 0

    codeact_agent.reset()

    # Create a mock for litellm_completion
    def check_headers(**kwargs):
        assert 'extra_headers' in kwargs
        assert 'anthropic-beta' in kwargs['extra_headers']
        assert kwargs['extra_headers']['anthropic-beta'] == 'prompt-caching-2024-07-31'
        # Create a mock response with the expected structure
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = 'Hello! How can I assist you today?'
        return mock_response

    # Use patch to replace litellm_completion with our check_headers function
    with patch('openhands.llm.llm.litellm_completion', side_effect=check_headers):
        # Also patch the action parser to return a MessageAction
        with patch.object(
            codeact_agent.action_parser,
            'parse',
            return_value=MessageAction('Hello! How can I assist you today?'),
        ):
            # Act
            result = codeact_agent.step(mock_state)

    # Assert
    assert isinstance(result, MessageAction)
    assert result.content == 'Hello! How can I assist you today?'
