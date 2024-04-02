import pytest
from opendevin.action import (
    action_from_dict,
    Action,
    AgentThinkAction,
    CmdKillAction,
    CmdRunAction,
    BrowseURLAction,
    FileReadAction,
    FileWriteAction,
    AgentRecallAction,
    AgentFinishAction,
    AddTaskAction,
    ModifyTaskAction,
)


def serialization_deserialization(original_action_dict, cls):
    action_instance = action_from_dict(original_action_dict)
    assert isinstance(
        action_instance, Action), 'The action instance should be an instance of Action.'
    assert isinstance(
        action_instance, cls), f'The action instance should be an instance of {cls.__name__}.'
    serialized_action_dict = action_instance.to_dict()
    serialized_action_dict.pop('message')
    assert serialized_action_dict == original_action_dict, 'The serialized action should match the original action dict.'


def test_agent_think_action_serialization_deserialization():
    original_action_dict = {
        'action': 'think',
        'args': {'thought': 'This is a test.'}
    }
    serialization_deserialization(original_action_dict, AgentThinkAction)


def test_agent_recall_action_serialization_deserialization():
    original_action_dict = {
        'action': 'recall',
        'args': {'query': 'Test query.'}
    }
    serialization_deserialization(original_action_dict, AgentRecallAction)


def test_agent_finish_action_serialization_deserialization():
    original_action_dict = {
        'action': 'finish',
        'args': {}
    }
    serialization_deserialization(original_action_dict, AgentFinishAction)


def test_cmd_kill_action_serialization_deserialization():
    original_action_dict = {
        'action': 'kill',
        'args': {'id': '1337'}
    }
    serialization_deserialization(original_action_dict, CmdKillAction)


def test_cmd_run_action_serialization_deserialization():
    original_action_dict = {
        'action': 'run',
        'args': {'command': 'echo "Hello world"', 'background': True}
    }
    serialization_deserialization(original_action_dict, CmdRunAction)


def test_browse_url_action_serialization_deserialization():
    original_action_dict = {
        'action': 'browse',
        'args': {'url': 'https://www.example.com'}
    }
    serialization_deserialization(original_action_dict, BrowseURLAction)


def test_file_read_action_serialization_deserialization():
    original_action_dict = {
        'action': 'read',
        'args': {'path': '/path/to/file.txt'}
    }
    serialization_deserialization(original_action_dict, FileReadAction)


def test_file_write_action_serialization_deserialization():
    original_action_dict = {
        'action': 'write',
        'args': {'path': '/path/to/file.txt', 'content': 'Hello world'}
    }
    serialization_deserialization(original_action_dict, FileWriteAction)


def test_add_task_action_serialization_deserialization():
    original_action_dict = {
        'action': 'add_task',
        'args': {'parent': 'Test parent', 'goal': 'Test goal', 'subtasks': []}
    }
    serialization_deserialization(original_action_dict, AddTaskAction)


def test_modify_task_action_serialization_deserialization():
    original_action_dict = {
        'action': 'modify_task',
        'args': {'id': 1, 'state': 'Test state.'}
    }
    serialization_deserialization(original_action_dict, ModifyTaskAction)
