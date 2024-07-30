import logging
from unittest.mock import Mock, patch

import pytest
from pytest import TempPathFactory

from opendevin.controller.agent_controller import AgentController
from opendevin.controller.state.state import State
from opendevin.controller.stuck import StuckDetector
from opendevin.events.action import CmdRunAction, FileReadAction, MessageAction
from opendevin.events.action.commands import IPythonRunCellAction
from opendevin.events.observation import (
    CmdOutputObservation,
    FileReadObservation,
)
from opendevin.events.observation.commands import IPythonRunCellObservation
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.error import ErrorObservation
from opendevin.events.stream import EventSource, EventStream
from opendevin.memory.history import ShortTermHistory
from opendevin.storage import get_file_store


def collect_events(stream):
    return [event for event in stream.get_events()]


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_is_stuck'))


@pytest.fixture
def event_stream(temp_dir):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('asdf', file_store)
    yield event_stream
    # clear after each test
    event_stream.clear()


class TestStuckDetector:
    @pytest.fixture
    def stuck_detector(self, event_stream):
        state = State(inputs={}, max_iterations=50)
        # state.history = ShortTermHistory()
        state.history.set_event_stream(event_stream)

        return StuckDetector(state)

    def test_history_too_short(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        message_action = MessageAction(content='Hello', wait_for_response=False)
        message_action._source = EventSource.USER
        observation = NullObservation(content='')
        observation._cause = message_action.id
        event_stream.add_event(message_action, EventSource.USER)
        event_stream.add_event(observation, EventSource.USER)

        cmd_action = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action, EventSource.AGENT)
        cmd_observation = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation._cause = cmd_action._id
        event_stream.add_event(cmd_observation, EventSource.USER)

        # stuck_detector.state.history.set_event_stream(event_stream)

        assert stuck_detector.is_stuck() is False

    def test_is_stuck_repeating_action_observation(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_observation = NullObservation('')

        # 2 events
        event_stream.add_event(hello_action, EventSource.USER)
        event_stream.add_event(hello_observation, EventSource.USER)

        cmd_action_1 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_1, EventSource.AGENT)
        cmd_observation_1 = CmdOutputObservation(
            content='', command='ls', command_id=cmd_action_1._id
        )
        cmd_observation_1._cause = cmd_action_1._id
        event_stream.add_event(cmd_observation_1, EventSource.USER)
        # 4 events

        cmd_action_2 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_2, EventSource.AGENT)
        cmd_observation_2 = CmdOutputObservation(
            content='', command='ls', command_id=cmd_action_2._id
        )
        cmd_observation_2._cause = cmd_action_2._id
        event_stream.add_event(cmd_observation_2, EventSource.USER)
        # 6 events

        # random user message just because we can
        message_null_observation = NullObservation(content='')
        event_stream.add_event(message_action, EventSource.USER)
        event_stream.add_event(message_null_observation, EventSource.USER)
        # 8 events

        assert stuck_detector.is_stuck() is False
        assert stuck_detector.state.almost_stuck == 2

        cmd_action_3 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_3, EventSource.AGENT)
        cmd_observation_3 = CmdOutputObservation(
            content='', command='ls', command_id=cmd_action_3._id
        )
        cmd_observation_3._cause = cmd_action_3._id
        event_stream.add_event(cmd_observation_3, EventSource.USER)
        # 10 events

        assert len(collect_events(event_stream)) == 10
        assert len(list(stuck_detector.state.history.get_events())) == 8
        assert len(stuck_detector.state.history.get_pairs()) == 5

        assert stuck_detector.is_stuck() is False
        assert stuck_detector.state.almost_stuck == 1

        cmd_action_4 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_4, EventSource.AGENT)
        cmd_observation_4 = CmdOutputObservation(
            content='', command='ls', command_id=cmd_action_4._id
        )
        cmd_observation_4._cause = cmd_action_4._id
        event_stream.add_event(cmd_observation_4, EventSource.USER)
        # 12 events

        assert len(collect_events(event_stream)) == 12
        assert len(list(stuck_detector.state.history.get_events())) == 10
        assert len(stuck_detector.state.history.get_pairs()) == 6

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck() is True
            assert stuck_detector.state.almost_stuck == 0
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_repeating_action_error(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        # (action, error_observation), not necessarily the same error
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_observation = NullObservation(content='')
        event_stream.add_event(hello_action, EventSource.USER)
        hello_observation._cause = hello_action._id
        event_stream.add_event(hello_observation, EventSource.USER)
        # 2 events

        cmd_action_1 = CmdRunAction(command='invalid_command')
        event_stream.add_event(cmd_action_1, EventSource.AGENT)
        error_observation_1 = ErrorObservation(content='Command not found')
        error_observation_1._cause = cmd_action_1._id
        event_stream.add_event(error_observation_1, EventSource.USER)
        # 4 events

        cmd_action_2 = CmdRunAction(command='invalid_command')
        event_stream.add_event(cmd_action_2, EventSource.AGENT)
        error_observation_2 = ErrorObservation(
            content='Command still not found or another error'
        )
        error_observation_2._cause = cmd_action_2._id
        event_stream.add_event(error_observation_2, EventSource.USER)
        # 6 events

        message_null_observation = NullObservation(content='')
        event_stream.add_event(message_action, EventSource.USER)
        event_stream.add_event(message_null_observation, EventSource.USER)
        # 8 events

        cmd_action_3 = CmdRunAction(command='invalid_command')
        event_stream.add_event(cmd_action_3, EventSource.AGENT)
        error_observation_3 = ErrorObservation(content='Different error')
        error_observation_3._cause = cmd_action_3._id
        event_stream.add_event(error_observation_3, EventSource.USER)
        # 10 events

        cmd_action_4 = CmdRunAction(command='invalid_command')
        event_stream.add_event(cmd_action_4, EventSource.AGENT)
        error_observation_4 = ErrorObservation(content='Command not found')
        error_observation_4._cause = cmd_action_4._id
        event_stream.add_event(error_observation_4, EventSource.USER)
        # 12 events

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck() is True
            mock_warning.assert_called_once_with(
                'Action, ErrorObservation loop detected'
            )

    def test_is_stuck_ipython_syntax_error(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        ipython_action_1 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_1, EventSource.AGENT)
        ipython_observation_1 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 1)',
            code='print("hello',
        )
        ipython_observation_1._cause = ipython_action_1._id
        event_stream.add_event(ipython_observation_1, EventSource.USER)

        ipython_action_2 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_2, EventSource.AGENT)
        ipython_observation_2 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 1)',
            code='print("hello',
        )
        ipython_observation_2._cause = ipython_action_2._id
        event_stream.add_event(ipython_observation_2, EventSource.USER)

        ipython_action_3 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_3, EventSource.AGENT)
        ipython_observation_3 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 3)',
            code='print("hello',
        )
        ipython_observation_3._cause = ipython_action_3._id
        event_stream.add_event(ipython_observation_3, EventSource.USER)

        ipython_action_4 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_4, EventSource.AGENT)
        ipython_observation_4 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 2)',
            code='print("hello',
        )
        ipython_observation_4._cause = ipython_action_4._id
        event_stream.add_event(ipython_observation_4, EventSource.USER)

        # stuck_detector.state.history.set_event_stream(event_stream)

        last_observations = [
            ipython_observation_1,
            ipython_observation_2,
            ipython_observation_3,
            ipython_observation_4,
        ]
        for observation in last_observations:
            has_string = (
                observation.content[-100:].find(
                    'SyntaxError: unterminated string literal (detected at line'
                )
                != -1
            )
            assert has_string

            string_is_last = (
                len(
                    observation.content.split(
                        'SyntaxError: unterminated string literal (detected at line'
                    )[-1]
                )
                < 10
            )
            assert string_is_last

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck() is True
            mock_warning.assert_called_once_with(
                'Action, IPythonRunCellObservation loop detected'
            )

    def test_is_stuck_ipython_syntax_error_not_at_end(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        ipython_action_1 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_1, EventSource.AGENT)
        ipython_observation_1 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 1)\nThis is some additional output',
            code='print("hello',
        )
        ipython_observation_1._cause = ipython_action_1._id
        event_stream.add_event(ipython_observation_1, EventSource.USER)

        ipython_action_2 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_2, EventSource.AGENT)
        ipython_observation_2 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 1)\nToo much output here on and on',
            code='print("hello',
        )
        ipython_observation_2._cause = ipython_action_2._id
        event_stream.add_event(ipython_observation_2, EventSource.USER)

        ipython_action_3 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_3, EventSource.AGENT)
        ipython_observation_3 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 3)\nEnough',
            code='print("hello',
        )
        ipython_observation_3._cause = ipython_action_3._id
        event_stream.add_event(ipython_observation_3, EventSource.USER)

        ipython_action_4 = IPythonRunCellAction(code='print("hello')
        event_stream.add_event(ipython_action_4, EventSource.AGENT)
        ipython_observation_4 = IPythonRunCellObservation(
            content='print("hello\n       ^\nSyntaxError: unterminated string literal (detected at line 2)\nLast line of output',
            code='print("hello',
        )
        ipython_observation_4._cause = ipython_action_4._id
        event_stream.add_event(ipython_observation_4, EventSource.USER)

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck() is False
            mock_warning.assert_not_called()

    def test_is_stuck_repeating_action_observation_pattern(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        message_action = MessageAction(content='Come on', wait_for_response=False)
        message_action._source = EventSource.USER
        event_stream.add_event(message_action, EventSource.USER)
        message_observation = NullObservation(content='')
        event_stream.add_event(message_observation, EventSource.USER)

        cmd_action_1 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_1, EventSource.AGENT)
        cmd_observation_1 = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_1._cause = cmd_action_1._id
        event_stream.add_event(cmd_observation_1, EventSource.USER)

        read_action_1 = FileReadAction(path='file1.txt')
        event_stream.add_event(read_action_1, EventSource.AGENT)
        read_observation_1 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_1._cause = read_action_1._id
        event_stream.add_event(read_observation_1, EventSource.USER)

        cmd_action_2 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_2, EventSource.AGENT)
        cmd_observation_2 = CmdOutputObservation(
            command_id=2, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_2._cause = cmd_action_2._id
        event_stream.add_event(cmd_observation_2, EventSource.USER)

        read_action_2 = FileReadAction(path='file1.txt')
        event_stream.add_event(read_action_2, EventSource.AGENT)
        read_observation_2 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_2._cause = read_action_2._id
        event_stream.add_event(read_observation_2, EventSource.USER)

        # one more message to break the pattern
        message_null_observation = NullObservation(content='')
        event_stream.add_event(message_action, EventSource.USER)
        event_stream.add_event(message_null_observation, EventSource.USER)

        cmd_action_3 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_3, EventSource.AGENT)
        cmd_observation_3 = CmdOutputObservation(
            command_id=3, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_3._cause = cmd_action_3._id
        event_stream.add_event(cmd_observation_3, EventSource.USER)

        read_action_3 = FileReadAction(path='file1.txt')
        event_stream.add_event(read_action_3, EventSource.AGENT)
        read_observation_3 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_3._cause = read_action_3._id
        event_stream.add_event(read_observation_3, EventSource.USER)

        with patch('logging.Logger.warning') as mock_warning:
            assert stuck_detector.is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation pattern detected')

    def test_is_stuck_not_stuck(
        self, stuck_detector: StuckDetector, event_stream: EventStream
    ):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        event_stream.add_event(hello_action, EventSource.USER)
        hello_observation = NullObservation(content='')
        hello_observation._cause = hello_action._id
        event_stream.add_event(hello_observation, EventSource.USER)

        cmd_action_1 = CmdRunAction(command='ls')
        event_stream.add_event(cmd_action_1, EventSource.AGENT)
        cmd_observation_1 = CmdOutputObservation(
            command_id=cmd_action_1.id, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_1._cause = cmd_action_1._id
        event_stream.add_event(cmd_observation_1, EventSource.USER)

        read_action_1 = FileReadAction(path='file1.txt')
        event_stream.add_event(read_action_1, EventSource.AGENT)
        read_observation_1 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_1._cause = read_action_1._id
        event_stream.add_event(read_observation_1, EventSource.USER)

        cmd_action_2 = CmdRunAction(command='pwd')
        event_stream.add_event(cmd_action_2, EventSource.AGENT)
        cmd_observation_2 = CmdOutputObservation(
            command_id=2, command='pwd', content='/home/user'
        )
        cmd_observation_2._cause = cmd_action_2._id
        event_stream.add_event(cmd_observation_2, EventSource.USER)

        read_action_2 = FileReadAction(path='file2.txt')
        event_stream.add_event(read_action_2, EventSource.AGENT)
        read_observation_2 = FileReadObservation(
            content='Another file content', path='file2.txt'
        )
        read_observation_2._cause = read_action_2._id
        event_stream.add_event(read_observation_2, EventSource.USER)

        message_null_observation = NullObservation(content='')
        event_stream.add_event(message_action, EventSource.USER)
        event_stream.add_event(message_null_observation, EventSource.USER)

        cmd_action_3 = CmdRunAction(command='pwd')
        event_stream.add_event(cmd_action_3, EventSource.AGENT)
        cmd_observation_3 = CmdOutputObservation(
            command_id=cmd_action_3.id, command='pwd', content='/home/user'
        )
        cmd_observation_3._cause = cmd_action_3._id
        event_stream.add_event(cmd_observation_3, EventSource.USER)

        read_action_3 = FileReadAction(path='file2.txt')
        event_stream.add_event(read_action_3, EventSource.AGENT)
        read_observation_3 = FileReadObservation(
            content='Another file content', path='file2.txt'
        )
        read_observation_3._cause = read_action_3._id
        event_stream.add_event(read_observation_3, EventSource.USER)

        assert stuck_detector.is_stuck() is False

    def test_is_stuck_monologue(self, stuck_detector, event_stream):
        # Add events to the event stream
        message_action_1 = MessageAction(content='Hi there!')
        event_stream.add_event(message_action_1, EventSource.USER)
        message_action_1._source = EventSource.USER

        message_action_2 = MessageAction(content='Hi there!')
        event_stream.add_event(message_action_2, EventSource.AGENT)
        message_action_2._source = EventSource.AGENT

        message_action_3 = MessageAction(content='How are you?')
        event_stream.add_event(message_action_3, EventSource.USER)
        message_action_3._source = EventSource.USER

        cmd_kill_action = CmdRunAction(
            command='echo 42', thought="I'm not stuck, he's stuck"
        )
        event_stream.add_event(cmd_kill_action, EventSource.AGENT)

        message_action_4 = MessageAction(content="I'm doing well, thanks for asking.")
        event_stream.add_event(message_action_4, EventSource.AGENT)
        message_action_4._source = EventSource.AGENT

        message_action_5 = MessageAction(content="I'm doing well, thanks for asking.")
        event_stream.add_event(message_action_5, EventSource.AGENT)
        message_action_5._source = EventSource.AGENT

        message_action_6 = MessageAction(content="I'm doing well, thanks for asking.")
        event_stream.add_event(message_action_6, EventSource.AGENT)
        message_action_6._source = EventSource.AGENT

        # stuck_detector.state.history.set_event_stream(event_stream)

        assert stuck_detector.is_stuck()

        # Add an observation event between the repeated message actions
        cmd_output_observation = CmdOutputObservation(
            content='OK, I was stuck, but no more.',
            command_id=42,
            command='storybook',
            exit_code=0,
        )
        cmd_output_observation._cause = cmd_kill_action._id
        event_stream.add_event(cmd_output_observation, EventSource.USER)

        message_action_7 = MessageAction(content="I'm doing well, thanks for asking.")
        event_stream.add_event(message_action_7, EventSource.AGENT)
        message_action_7._source = EventSource.AGENT

        message_action_8 = MessageAction(content="I'm doing well, thanks for asking.")
        event_stream.add_event(message_action_8, EventSource.AGENT)
        message_action_8._source = EventSource.AGENT

        assert not stuck_detector.is_stuck()


class TestAgentController:
    @pytest.fixture
    def controller(self):
        controller = Mock(spec=AgentController)
        controller._is_stuck = AgentController._is_stuck.__get__(
            controller, AgentController
        )
        controller.delegate = None
        controller.state = Mock()
        controller.state.history = ShortTermHistory()
        return controller

    def test_is_stuck_delegate_stuck(self, controller: AgentController):
        controller.delegate = Mock()
        controller.delegate._is_stuck.return_value = True
        assert controller._is_stuck() is True
