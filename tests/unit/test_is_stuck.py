from unittest.mock import Mock, patch

import pytest

from opendevin.controller.agent_controller import AgentController
from opendevin.events.action import CmdRunAction, FileReadAction, MessageAction
from opendevin.events.observation import CmdOutputObservation, Observation
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.error import ErrorObservation
from opendevin.events.stream import EventSource


class TestAgentController:
    @pytest.fixture
    def controller(self):
        controller = Mock(spec=AgentController)
        controller._is_stuck = AgentController._is_stuck.__get__(
            controller, AgentController
        )
        controller.delegate = None
        controller.state = Mock()
        controller.state.history = []
        return controller

    def test_history_too_short(self, controller):
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
        ]
        assert controller._is_stuck() is False

    def test_is_stuck_repeating_action_null_observation(self, controller):
        # message actions with source USER are not considered in the stuck check
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (CmdRunAction(command='ls'), NullObservation(content='')),
            (CmdRunAction(command='ls'), NullObservation(content='')),
            (message_action, NullObservation(content='')),
            (CmdRunAction(command='ls'), NullObservation(content='')),
            (CmdRunAction(command='ls'), NullObservation(content='')),
        ]
        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_repeating_action_error_observation(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='invalid_command'),
                ErrorObservation(content='Command not found'),
            ),
            (
                CmdRunAction(command='invalid_command'),
                ErrorObservation(content='Command not found'),
            ),
            (message_action, NullObservation(content='')),
            (
                CmdRunAction(command='invalid_command'),
                ErrorObservation(content='Different error'),
            ),
            (
                CmdRunAction(command='invalid_command'),
                ErrorObservation(content='Command not found'),
            ),
        ]
        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with(
                'Action, ErrorObservation loop detected'
            )

    def test_is_stuck_repeating_action_observation_pattern(self, controller):
        message_action = MessageAction(content='Come on', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=2, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
            (message_action, NullObservation(content='')),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=3, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
        ]
        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation pattern detected')

    def test_is_stuck_not_stuck(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
            (
                CmdRunAction(command='pwd'),
                CmdOutputObservation(command_id=2, command='pwd', content='/home/user'),
            ),
            (
                FileReadAction(path='file2.txt'),
                Observation(content='Another file content'),
            ),
            (message_action, NullObservation(content='')),
            (
                CmdRunAction(command='pwd'),
                CmdOutputObservation(command_id=3, command='pwd', content='/home/user'),
            ),
            (
                FileReadAction(path='file2.txt'),
                Observation(content='Another file content'),
            ),
        ]
        assert controller._is_stuck() is False

    def test_is_stuck_identical_tuples(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (message_action, NullObservation(content='')),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
        ]
        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_repeating_pattern_six_tuples(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        controller.state.history = [
            (
                MessageAction(content='Hello', wait_for_response=False),
                Observation(content='Response 1'),
            ),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=1, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=2, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
            (message_action, NullObservation(content='')),
            (
                CmdRunAction(command='ls'),
                CmdOutputObservation(
                    command_id=3, command='ls', content='file1.txt\nfile2.txt'
                ),
            ),
            (FileReadAction(path='file1.txt'), Observation(content='File content')),
        ]
        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation pattern detected')

    def test_is_stuck_delegate_stuck(self, controller):
        controller.delegate = Mock()
        controller.delegate._is_stuck.return_value = True
        assert controller._is_stuck() is True
