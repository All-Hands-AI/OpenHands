from unittest.mock import Mock, patch

import pytest

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig
from openhands.core.message import ImageContent, TextContent
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import EventSource
from openhands.events.observation.commands import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation


@pytest.fixture
def agent():
    with patch('openhands.llm.llm.LLM', autospec=True) as MockLLM:
        mock_llm = MockLLM.return_value
        mock_llm.is_caching_prompt_active.return_value = False
        mock_llm.config = Mock(max_message_chars=100)
        mock_llm.completion = Mock()
        mock_llm.vision_is_active.return_value = False
        agent = CodeActAgent(llm=mock_llm, config=AgentConfig())
        yield agent


def test_cmd_output_observation_message(agent: CodeActAgent):
    obs = CmdOutputObservation(
        command='echo hello', content='Command output', command_id=1, exit_code=0
    )

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Command output' in result.content[0].text
    assert 'Command 1 finished with exit code 0' in result.content[0].text


def test_ipython_run_cell_observation_message(agent: CodeActAgent):
    obs = IPythonRunCellObservation(
        code='plt.plot()',
        content=r'IPython output\n![image](data:image/png;base64,ABC123)\nMore output',
    )
    agent.llm.config.max_message_chars = 200
    result = agent.get_observation_message(obs)
    print(result)
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)

    expected_content = (
        r'OBSERVATION:\n'
        r'IPython output\n'
        r'![image](data:image/png;base64, ...) already displayed to user\n'
        'More output'
    )
    assert result.content[0].text == expected_content
    assert 'ABC123' not in result.content[0].text


def test_agent_delegate_observation_message(agent: CodeActAgent):
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Delegated agent output' in result.content[0].text


def test_error_observation_message(agent: CodeActAgent):
    obs = ErrorObservation('Error message')

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Error message' in result.content[0].text
    assert 'Error occurred in processing last action' in result.content[0].text


def test_unknown_observation_message(agent: CodeActAgent):
    obs = Mock()

    with pytest.raises(ValueError, match='Unknown observation type:'):
        agent.get_observation_message(obs)


def test_action_to_str(agent: CodeActAgent):
    # Test CmdRunAction
    cmd_action = CmdRunAction(command='ls -l', thought='List files')
    assert (
        agent.action_to_str(cmd_action)
        == 'List files\n<execute_bash>\nls -l\n</execute_bash>'
    )

    # Test IPythonRunCellAction
    ipython_action = IPythonRunCellAction(
        code='print("Hello")', thought='Print greeting'
    )
    assert (
        agent.action_to_str(ipython_action)
        == 'Print greeting\n<execute_ipython>\nprint("Hello")\n</execute_ipython>'
    )

    # Test AgentDelegateAction
    delegate_action = AgentDelegateAction(
        agent='web_search', inputs={'task': 'Search web'}, thought='Delegate search'
    )
    assert (
        agent.action_to_str(delegate_action)
        == 'Delegate search\n<execute_browse>\nSearch web\n</execute_browse>'
    )

    # Test MessageAction
    message_action = MessageAction(content='User message')
    assert agent.action_to_str(message_action) == 'User message'

    # Test AgentFinishAction
    # myevent = Event(source=EventSource.AGENT, message='Task complete')
    finish_action = AgentFinishAction(thought='Task complete')
    finish_action._source = EventSource.AGENT
    assert agent.action_to_str(finish_action) == 'Task complete'


def test_get_action_message(agent: CodeActAgent):
    # Test CmdRunAction
    cmd_action = CmdRunAction(command='ls -l', thought='List files')
    cmd_message = agent.get_action_message(cmd_action)
    assert cmd_message.role == 'assistant'
    assert (
        cmd_message.content[0].text
        == 'List files\n<execute_bash>\nls -l\n</execute_bash>'
    )

    # Test MessageAction with images
    agent.llm.vision_is_active = lambda: True
    message_action = MessageAction(
        content='Image description', images_urls=['http://example.com/image.jpg']
    )
    message = agent.get_action_message(message_action)
    assert message.role == 'assistant'
    assert message.content[0].text == 'Image description'
    assert isinstance(message.content[1], ImageContent)
    assert message.content[1].image_urls == ['http://example.com/image.jpg']

    # Test AgentFinishAction from user
    finish_action = AgentFinishAction(thought='User finished')
    finish_message = agent.get_action_message(finish_action)
    assert (
        finish_message is None
    ), 'AgentFinishAction should not be returned as a message'


def test_reset(agent: CodeActAgent):
    # Set some state
    agent._complete = True

    # Call reset
    agent.reset()

    # Check that the state has been reset
    assert not agent.complete, 'Agent complete should be reset to False'


def test_step(agent: CodeActAgent):
    state = Mock()
    state.history.get_last_user_message.return_value = None
    state.history.get_events.return_value = []
    state.max_iterations = 10
    state.iteration = 0

    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                content='Test response\n<execute_bash>\necho "Hello"\n</execute_bash>'
            )
        )
    ]

    with patch.object(agent.llm, 'completion') as mock_completion:
        mock_completion.return_value = mock_response

        action = agent.step(state)

        assert isinstance(action, CmdRunAction)
        assert action.command == 'echo "Hello"'
        assert action.thought == 'Test response'

    # Test /exit command
    state.history.get_last_user_message.return_value = '/exit'
    action = agent.step(state)
    assert isinstance(action, AgentFinishAction)


def test_step_error_handling(agent: CodeActAgent):
    state = Mock()
    state.history.get_last_user_message.return_value = ''
    state.history.get_events.return_value = []
    state.max_iterations = 10
    state.iteration = 3

    with patch.object(agent.llm, 'completion') as mock_completion:
        mock_completion.side_effect = Exception('Test error')

        action = agent.step(state)

    assert isinstance(action, AgentFinishAction)
    assert 'Agent encountered an error' in action.thought
    assert 'Test error' in action.thought
