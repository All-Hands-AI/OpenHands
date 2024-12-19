from openhands.events.action import (
    Action,
    AddTaskAction,
    AgentFinishAction,
    AgentRejectAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
    ModifyTaskAction,
)
from openhands.events.action.action import ActionConfirmationStatus
from openhands.events.serialization import (
    event_from_dict,
    event_to_dict,
    event_to_memory,
)


def serialization_deserialization(
    original_action_dict, cls, max_message_chars: int = 10000
):
    action_instance = event_from_dict(original_action_dict)
    assert isinstance(
        action_instance, Action
    ), 'The action instance should be an instance of Action.'
    assert isinstance(
        action_instance, cls
    ), f'The action instance should be an instance of {cls.__name__}.'

    # event_to_dict is the regular serialization of an event
    serialized_action_dict = event_to_dict(action_instance)

    # it has an extra message property, for the UI
    serialized_action_dict.pop('message')
    assert (
        serialized_action_dict == original_action_dict
    ), 'The serialized action should match the original action dict.'

    # memory dict is what is sent to the LLM
    serialized_action_memory = event_to_memory(action_instance, max_message_chars)
    original_memory_dict = original_action_dict.copy()

    # we don't send backend properties like id or 'keep_prompt'
    original_memory_dict.pop('id', None)
    original_memory_dict.pop('timestamp', None)
    if 'args' in original_memory_dict:
        original_memory_dict['args'].pop('keep_prompt', None)
        original_memory_dict['args'].pop('blocking', None)
        original_memory_dict['args'].pop('confirmation_state', None)

    # the rest should match
    assert (
        serialized_action_memory == original_memory_dict
    ), 'The serialized action in memory should match the original action dict.'


def test_event_props_serialization_deserialization():
    original_action_dict = {
        'id': 42,
        'source': 'agent',
        'timestamp': '2021-08-01T12:00:00',
        'action': 'message',
        'args': {
            'content': 'This is a test.',
            'image_urls': None,
            'wait_for_response': False,
        },
    }
    serialization_deserialization(original_action_dict, MessageAction)


def test_message_action_serialization_deserialization():
    original_action_dict = {
        'action': 'message',
        'args': {
            'content': 'This is a test.',
            'image_urls': None,
            'wait_for_response': False,
        },
    }
    serialization_deserialization(original_action_dict, MessageAction)


def test_agent_finish_action_serialization_deserialization():
    original_action_dict = {'action': 'finish', 'args': {'outputs': {}, 'thought': ''}}
    serialization_deserialization(original_action_dict, AgentFinishAction)


def test_agent_reject_action_serialization_deserialization():
    original_action_dict = {'action': 'reject', 'args': {'outputs': {}, 'thought': ''}}
    serialization_deserialization(original_action_dict, AgentRejectAction)


def test_cmd_run_action_serialization_deserialization():
    original_action_dict = {
        'action': 'run',
        'args': {
            'blocking': False,
            'command': 'echo "Hello world"',
            'thought': '',
            'keep_prompt': True,
            'hidden': False,
            'confirmation_state': ActionConfirmationStatus.CONFIRMED,
        },
    }
    serialization_deserialization(original_action_dict, CmdRunAction)


def test_browse_url_action_serialization_deserialization():
    original_action_dict = {
        'action': 'browse',
        'args': {'thought': '', 'url': 'https://www.example.com'},
    }
    serialization_deserialization(original_action_dict, BrowseURLAction)


def test_browse_interactive_action_serialization_deserialization():
    original_action_dict = {
        'action': 'browse_interactive',
        'args': {
            'thought': '',
            'browser_actions': 'goto("https://www.example.com")',
            'browsergym_send_msg_to_user': '',
        },
    }
    serialization_deserialization(original_action_dict, BrowseInteractiveAction)


def test_file_read_action_serialization_deserialization():
    original_action_dict = {
        'action': 'read',
        'args': {
            'path': '/path/to/file.txt',
            'start': 0,
            'end': -1,
            'thought': 'None',
            'impl_source': 'default',
            'translated_ipython_code': '',
        },
    }
    serialization_deserialization(original_action_dict, FileReadAction)


def test_file_write_action_serialization_deserialization():
    original_action_dict = {
        'action': 'write',
        'args': {
            'path': '/path/to/file.txt',
            'content': 'Hello world',
            'start': 0,
            'end': 1,
            'thought': 'None',
        },
    }
    serialization_deserialization(original_action_dict, FileWriteAction)


def test_add_task_action_serialization_deserialization():
    original_action_dict = {
        'action': 'add_task',
        'args': {
            'parent': 'Test parent',
            'goal': 'Test goal',
            'subtasks': [],
            'thought': '',
        },
    }
    serialization_deserialization(original_action_dict, AddTaskAction)


def test_modify_task_action_serialization_deserialization():
    original_action_dict = {
        'action': 'modify_task',
        'args': {'task_id': 1, 'state': 'Test state.', 'thought': ''},
    }
    serialization_deserialization(original_action_dict, ModifyTaskAction)
