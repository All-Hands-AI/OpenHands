from unittest.mock import Mock, patch

import pytest

from opendevin.controller.agent_controller import AgentController
from opendevin.events.action import CmdRunAction, FileReadAction, MessageAction
from opendevin.events.action.commands import CmdKillAction
from opendevin.events.observation import (
    CmdOutputObservation,
    FileReadObservation,
    Observation,
)
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.error import ErrorObservation
from opendevin.events.stream import EventSource
from opendevin.memory.history import ShortTermHistory


class TestAgentController:
    @pytest.fixture
    def controller(self):
        controller = Mock(spec=AgentController)
        controller._is_stuck = AgentController._is_stuck.__get__(
            controller, AgentController
        )
        controller._eq_no_pid = AgentController._eq_no_pid.__get__(
            controller, AgentController
        )
        controller.delegate = None
        controller.state = Mock()
        controller.state.history = ShortTermHistory()
        return controller

    def test_history_too_short(self, controller):
        message_action = MessageAction(content='Hello', wait_for_response=False)
        message_action._id = 1
        observation = Observation(content='Response 1')
        observation._cause = message_action._id
        controller.state.history.append((message_action, observation))

        cmd_action = CmdRunAction(command='ls')
        cmd_action._id = 2
        cmd_observation = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation._cause = cmd_action._id
        controller.state.history.append((cmd_action, cmd_observation))

        assert controller._is_stuck() is False

    def test_is_stuck_repeating_action_null_observation(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_action._id = 2
        hello_observation = Observation(content='Response 1')
        controller.state.history.append((hello_action, hello_observation))

        cmd_action_1 = CmdRunAction(command='ls')
        cmd_action_1._id = 3
        null_observation_1 = NullObservation(content='')
        null_observation_1._cause = cmd_action_1._id
        controller.state.history.append((cmd_action_1, null_observation_1))

        cmd_action_2 = CmdRunAction(command='ls')
        cmd_action_2._id = 4
        null_observation_2 = NullObservation(content='')
        null_observation_2._cause = cmd_action_2._id
        controller.state.history.append((cmd_action_2, null_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_action_3 = CmdRunAction(command='ls')
        cmd_action_3._id = 5
        null_observation_3 = NullObservation(content='')
        null_observation_3._cause = cmd_action_3._id
        controller.state.history.append((cmd_action_3, null_observation_3))

        cmd_action_4 = CmdRunAction(command='ls')
        cmd_action_4._id = 6
        null_observation_4 = NullObservation(content='')
        null_observation_4._cause = cmd_action_4._id
        controller.state.history.append((cmd_action_4, null_observation_4))

        assert len(controller.state.history) == 12
        assert len(controller.state.history.get_tuples()) == 6

        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_repeating_action_error_observation(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_action._id = 2
        hello_observation = Observation(content='Response 1')
        hello_observation._cause = hello_action._id
        controller.state.history.append((hello_action, hello_observation))

        cmd_action_1 = CmdRunAction(command='invalid_command')
        cmd_action_1._id = 3
        error_observation_1 = ErrorObservation(content='Command not found')
        error_observation_1._cause = cmd_action_1._id
        controller.state.history.append((cmd_action_1, error_observation_1))

        cmd_action_2 = CmdRunAction(command='invalid_command')
        cmd_action_2._id = 4
        error_observation_2 = ErrorObservation(
            content='Command still not found or another error'
        )
        error_observation_2._cause = cmd_action_2._id
        controller.state.history.append((cmd_action_2, error_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_action_3 = CmdRunAction(command='invalid_command')
        cmd_action_3._id = 5
        error_observation_3 = ErrorObservation(content='Different error')
        error_observation_3._cause = cmd_action_3._id
        controller.state.history.append((cmd_action_3, error_observation_3))

        cmd_action_4 = CmdRunAction(command='invalid_command')
        cmd_action_4._id = 6
        error_observation_4 = ErrorObservation(content='Command not found')
        error_observation_4._cause = cmd_action_4._id
        controller.state.history.append((cmd_action_4, error_observation_4))

        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with(
                'Action, ErrorObservation loop detected'
            )

    def test_is_stuck_repeating_action_observation_pattern(self, controller):
        message_action = MessageAction(content='Come on', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1
        message_observation = Observation(content='')
        controller.state.history.append((message_action, message_observation))

        cmd_action_1 = CmdRunAction(command='ls')
        cmd_action_1._id = 2
        cmd_observation_1 = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_1._cause = cmd_action_1._id
        controller.state.history.append((cmd_action_1, cmd_observation_1))

        read_action_1 = FileReadAction(path='file1.txt')
        read_action_1._id = 3
        read_observation_1 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_1._cause = read_action_1._id
        controller.state.history.append((read_action_1, read_observation_1))

        cmd_action_2 = CmdRunAction(command='ls')
        cmd_action_2._id = 4
        cmd_observation_2 = CmdOutputObservation(
            command_id=2, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_2._cause = cmd_action_2._id
        controller.state.history.append((cmd_action_2, cmd_observation_2))

        read_action_2 = FileReadAction(path='file1.txt')
        read_action_2._id = 5
        read_observation_2 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_2._cause = read_action_2._id
        controller.state.history.append((read_action_2, read_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_action_3 = CmdRunAction(command='ls')
        cmd_action_3._id = 6
        cmd_observation_3 = CmdOutputObservation(
            command_id=3, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_3._cause = cmd_action_3._id
        controller.state.history.append((cmd_action_3, cmd_observation_3))

        read_action_3 = FileReadAction(path='file1.txt')
        read_action_3._id = 7
        read_observation_3 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_3._cause = read_action_3._id
        controller.state.history.append((read_action_3, read_observation_3))

        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation pattern detected')

    def test_is_stuck_not_stuck(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_action._id = 2
        hello_observation = Observation(content='Response 1')
        hello_observation._cause = hello_action._id
        controller.state.history.append((hello_action, hello_observation))

        cmd_action_1 = CmdRunAction(command='ls')
        cmd_action_1._id = 3
        cmd_observation_1 = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_1._cause = cmd_action_1._id
        controller.state.history.append((cmd_action_1, cmd_observation_1))

        read_action_1 = FileReadAction(path='file1.txt')
        read_action_1._id = 4
        read_observation_1 = FileReadObservation(
            content='File content', path='file1.txt'
        )
        read_observation_1._cause = read_action_1._id
        controller.state.history.append((read_action_1, read_observation_1))

        cmd_action_2 = CmdRunAction(command='pwd')
        cmd_action_2._id = 5
        cmd_observation_2 = CmdOutputObservation(
            command_id=2, command='pwd', content='/home/user'
        )
        cmd_observation_2._cause = cmd_action_2._id
        controller.state.history.append((cmd_action_2, cmd_observation_2))

        read_action_2 = FileReadAction(path='file2.txt')
        read_action_2._id = 6
        read_observation_2 = Observation(content='Another file content')
        read_observation_2._cause = read_action_2._id
        controller.state.history.append((read_action_2, read_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_action_3 = CmdRunAction(command='pwd')
        cmd_action_3._id = 7
        cmd_observation_3 = CmdOutputObservation(
            command_id=3, command='pwd', content='/home/user'
        )
        cmd_observation_3._cause = cmd_action_3._id
        controller.state.history.append((cmd_action_3, cmd_observation_3))

        read_action_3 = FileReadAction(path='file2.txt')
        read_action_3._id = 8
        read_observation_3 = Observation(content='Another file content')
        read_observation_3._cause = read_action_3._id
        controller.state.history.append((read_action_3, read_observation_3))

        assert controller._is_stuck() is False

    def test_is_stuck_four_identical_tuples(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_action._id = 2
        hello_observation = Observation(content='Response 1')
        hello_observation._cause = hello_action._id
        controller.state.history.append((hello_action, hello_observation))

        cmd_action_1 = CmdRunAction(command='ls')
        cmd_action_1._id = 3
        cmd_observation_1 = CmdOutputObservation(
            command_id=1, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_1._cause = cmd_action_1._id
        controller.state.history.append((cmd_action_1, cmd_observation_1))

        cmd_action_2 = CmdRunAction(command='ls')
        cmd_action_2._id = 4
        cmd_observation_2 = CmdOutputObservation(
            command_id=2, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_2._cause = cmd_action_2._id
        controller.state.history.append((cmd_action_2, cmd_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_action_3 = CmdRunAction(command='ls')
        cmd_action_3._id = 5
        cmd_observation_3 = CmdOutputObservation(
            command_id=3, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_3._cause = cmd_action_3._id
        controller.state.history.append((cmd_action_3, cmd_observation_3))

        cmd_action_4 = CmdRunAction(command='ls')
        cmd_action_4._id = 6
        cmd_observation_4 = CmdOutputObservation(
            command_id=4, command='ls', content='file1.txt\nfile2.txt'
        )
        cmd_observation_4._cause = cmd_action_4._id
        controller.state.history.append((cmd_action_4, cmd_observation_4))

        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_four_tuples_cmd_kill_and_output(self, controller):
        message_action = MessageAction(content='Done', wait_for_response=False)
        message_action._source = EventSource.USER
        message_action._id = 1

        hello_action = MessageAction(content='Hello', wait_for_response=False)
        hello_action._id = 2
        hello_observation = Observation(content='Response 1')
        hello_observation._cause = hello_action._id
        controller.state.history.append((hello_action, hello_observation))

        cmd_kill_action_1 = CmdKillAction(
            command_id=1, thought='It looks like storybook is stuck, lets kill it'
        )
        cmd_kill_action_1._id = 3
        cmd_output_observation_1 = CmdOutputObservation(
            content='Background command storybook has been killed.',
            command_id=1,
            command='storybook',
            exit_code=0,
        )
        cmd_output_observation_1._cause = cmd_kill_action_1._id
        controller.state.history.append((cmd_kill_action_1, cmd_output_observation_1))

        cmd_kill_action_2 = CmdKillAction(
            command_id=2, thought='It looks like storybook is stuck, lets kill it'
        )
        cmd_kill_action_2._id = 4
        cmd_output_observation_2 = CmdOutputObservation(
            content='Background command storybook has been killed.',
            command_id=2,
            command='storybook',
            exit_code=0,
        )
        cmd_output_observation_2._cause = cmd_kill_action_2._id
        controller.state.history.append((cmd_kill_action_2, cmd_output_observation_2))

        message_null_observation = NullObservation(content='')
        controller.state.history.append((message_action, message_null_observation))

        cmd_kill_action_3 = CmdKillAction(
            command_id=3, thought='It looks like storybook is stuck, lets kill it'
        )
        cmd_kill_action_3._id = 5
        cmd_output_observation_3 = CmdOutputObservation(
            content='Background command storybook has been killed.',
            command_id=3,
            command='storybook',
            exit_code=0,
        )
        cmd_output_observation_3._cause = cmd_kill_action_3._id
        controller.state.history.append((cmd_kill_action_3, cmd_output_observation_3))

        cmd_kill_action_4 = CmdKillAction(
            command_id=4, thought='It looks like storybook is stuck, lets kill it'
        )
        cmd_kill_action_4._id = 6
        cmd_output_observation_4 = CmdOutputObservation(
            content='Background command storybook has been killed.',
            command_id=4,
            command='storybook',
            exit_code=0,
        )
        cmd_output_observation_4._cause = cmd_kill_action_4._id
        controller.state.history.append((cmd_kill_action_4, cmd_output_observation_4))

        with patch('logging.Logger.warning') as mock_warning:
            assert controller._is_stuck() is True
            mock_warning.assert_called_once_with('Action, Observation loop detected')

    def test_is_stuck_delegate_stuck(self, controller):
        controller.delegate = Mock()
        controller.delegate._is_stuck.return_value = True
        assert controller._is_stuck() is True
