from openhands.events.action import (
    Action,
    AgentFinishAction,
    AgentRejectAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
    RecallAction,
)
from openhands.events.action.action import ActionConfirmationStatus
from openhands.events.action.files import FileEditSource, FileReadSource
from openhands.events.serialization import (
    event_from_dict,
    event_to_dict,
)


def serialization_deserialization(
    original_action_dict, cls, max_message_chars: int = 10000
):
    action_instance = event_from_dict(original_action_dict)
    assert isinstance(action_instance, Action), (
        'The action instance should be an instance of Action.'
    )
    assert isinstance(action_instance, cls), (
        f'The action instance should be an instance of {cls.__name__}.'
    )

    # event_to_dict is the regular serialization of an event
    serialized_action_dict = event_to_dict(action_instance)

    # it has an extra message property, for the UI
    serialized_action_dict.pop('message')
    assert serialized_action_dict == original_action_dict, (
        'The serialized action should match the original action dict.'
    )


def test_event_props_serialization_deserialization():
    original_action_dict = {
        'id': 42,
        'source': 'agent',
        'timestamp': '2021-08-01T12:00:00',
        'action': 'message',
        'args': {
            'content': 'This is a test.',
            'image_urls': None,
            'file_urls': None,
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
            'file_urls': None,
            'wait_for_response': False,
        },
    }
    serialization_deserialization(original_action_dict, MessageAction)


def test_agent_finish_action_serialization_deserialization():
    original_action_dict = {
        'action': 'finish',
        'args': {
            'outputs': {},
            'thought': '',
            'task_completed': None,
            'final_thought': '',
        },
    }
    serialization_deserialization(original_action_dict, AgentFinishAction)


def test_agent_reject_action_serialization_deserialization():
    original_action_dict = {
        'action': 'reject',
        'args': {'outputs': {}, 'thought': ''},
    }
    serialization_deserialization(original_action_dict, AgentRejectAction)


def test_cmd_run_action_serialization_deserialization():
    original_action_dict = {
        'action': 'run',
        'args': {
            'blocking': False,
            'command': 'echo "Hello world"',
            'is_input': False,
            'thought': '',
            'hidden': False,
            'confirmation_state': ActionConfirmationStatus.CONFIRMED,
            'is_static': False,
            'cwd': None,
        },
    }
    serialization_deserialization(original_action_dict, CmdRunAction)


def test_browse_url_action_serialization_deserialization():
    original_action_dict = {
        'action': 'browse',
        'args': {
            'thought': '',
            'url': 'https://www.example.com',
            'return_axtree': False,
        },
    }
    serialization_deserialization(original_action_dict, BrowseURLAction)


def test_browse_interactive_action_serialization_deserialization():
    original_action_dict = {
        'action': 'browse_interactive',
        'args': {
            'thought': '',
            'browser_actions': 'goto("https://www.example.com")',
            'browsergym_send_msg_to_user': '',
            'return_axtree': False,
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
            'view_range': None,
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


def test_file_edit_action_aci_serialization_deserialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/path/to/file.txt',
            'command': 'str_replace',
            'file_text': None,
            'old_str': 'old text',
            'new_str': 'new text',
            'insert_line': None,
            'content': '',
            'start': 1,
            'end': -1,
            'thought': 'Replacing text',
            'impl_source': 'oh_aci',
        },
    }
    serialization_deserialization(original_action_dict, FileEditAction)


def test_file_edit_action_llm_serialization_deserialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/path/to/file.txt',
            'command': None,
            'file_text': None,
            'old_str': None,
            'new_str': None,
            'insert_line': None,
            'content': 'Updated content',
            'start': 1,
            'end': 10,
            'thought': 'Updating file content',
            'impl_source': 'llm_based_edit',
        },
    }
    serialization_deserialization(original_action_dict, FileEditAction)


def test_cmd_run_action_legacy_serialization():
    original_action_dict = {
        'action': 'run',
        'args': {
            'blocking': False,
            'command': 'echo "Hello world"',
            'thought': '',
            'hidden': False,
            'confirmation_state': ActionConfirmationStatus.CONFIRMED,
            'keep_prompt': False,  # will be treated as no-op
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, CmdRunAction)
    assert event.command == 'echo "Hello world"'
    assert event.hidden is False
    assert not hasattr(event, 'keep_prompt')

    event_dict = event_to_dict(event)
    assert 'keep_prompt' not in event_dict['args']
    assert (
        event_dict['args']['confirmation_state'] == ActionConfirmationStatus.CONFIRMED
    )
    assert event_dict['args']['blocking'] is False
    assert event_dict['args']['command'] == 'echo "Hello world"'
    assert event_dict['args']['thought'] == ''
    assert event_dict['args']['is_input'] is False


def test_file_llm_based_edit_action_legacy_serialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/path/to/file.txt',
            'content': 'dummy content',
            'start': 1,
            'end': -1,
            'thought': 'Replacing text',
            'impl_source': 'oh_aci',
            'translated_ipython_code': None,
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileEditAction)

    # Common arguments
    assert event.path == '/path/to/file.txt'
    assert event.thought == 'Replacing text'
    assert event.impl_source == FileEditSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')

    # OH_ACI arguments
    assert event.command == ''
    assert event.file_text is None
    assert event.old_str is None
    assert event.new_str is None
    assert event.insert_line is None

    # LLM-based editing arguments
    assert event.content == 'dummy content'
    assert event.start == 1
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']

    # Common arguments
    assert event_dict['args']['path'] == '/path/to/file.txt'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert event_dict['args']['thought'] == 'Replacing text'

    # OH_ACI arguments
    assert event_dict['args']['command'] == ''
    assert event_dict['args']['file_text'] is None
    assert event_dict['args']['old_str'] is None
    assert event_dict['args']['new_str'] is None
    assert event_dict['args']['insert_line'] is None

    # LLM-based editing arguments
    assert event_dict['args']['content'] == 'dummy content'
    assert event_dict['args']['start'] == 1
    assert event_dict['args']['end'] == -1


def test_file_ohaci_edit_action_legacy_serialization():
    original_action_dict = {
        'action': 'edit',
        'args': {
            'path': '/workspace/game_2048.py',
            'content': '',
            'start': 1,
            'end': -1,
            'thought': "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file.",
            'impl_source': 'oh_aci',
            'translated_ipython_code': "print(file_editor(**{'command': 'create', 'path': '/workspace/game_2048.py', 'file_text': 'New file content'}))",
        },
    }
    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileEditAction)

    # Common arguments
    assert event.path == '/workspace/game_2048.py'
    assert (
        event.thought
        == "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file."
    )
    assert event.impl_source == FileEditSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')

    # OH_ACI arguments
    assert event.command == 'create'
    assert event.file_text == 'New file content'
    assert event.old_str is None
    assert event.new_str is None
    assert event.insert_line is None

    # LLM-based editing arguments
    assert event.content == ''
    assert event.start == 1
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']

    # Common arguments
    assert event_dict['args']['path'] == '/workspace/game_2048.py'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert (
        event_dict['args']['thought']
        == "I'll help you create a simple 2048 game in Python. I'll use the str_replace_editor to create the file."
    )

    # OH_ACI arguments
    assert event_dict['args']['command'] == 'create'
    assert event_dict['args']['file_text'] == 'New file content'
    assert event_dict['args']['old_str'] is None
    assert event_dict['args']['new_str'] is None
    assert event_dict['args']['insert_line'] is None

    # LLM-based editing arguments
    assert event_dict['args']['content'] == ''
    assert event_dict['args']['start'] == 1
    assert event_dict['args']['end'] == -1


def test_agent_microagent_action_serialization_deserialization():
    original_action_dict = {
        'action': 'recall',
        'args': {
            'query': 'What is the capital of France?',
            'thought': 'I need to find information about France',
            'recall_type': 'knowledge',
        },
    }
    serialization_deserialization(original_action_dict, RecallAction)


def test_file_read_action_legacy_serialization():
    original_action_dict = {
        'action': 'read',
        'args': {
            'path': '/workspace/test.txt',
            'start': 0,
            'end': -1,
            'thought': 'Reading the file contents',
            'impl_source': 'oh_aci',
            'translated_ipython_code': "print(file_editor(**{'command': 'view', 'path': '/workspace/test.txt'}))",
        },
    }

    event = event_from_dict(original_action_dict)
    assert isinstance(event, Action)
    assert isinstance(event, FileReadAction)

    # Common arguments
    assert event.path == '/workspace/test.txt'
    assert event.thought == 'Reading the file contents'
    assert event.impl_source == FileReadSource.OH_ACI
    assert not hasattr(event, 'translated_ipython_code')
    assert not hasattr(
        event, 'command'
    )  # FileReadAction should not have command attribute

    # Read-specific arguments
    assert event.start == 0
    assert event.end == -1

    event_dict = event_to_dict(event)
    assert 'translated_ipython_code' not in event_dict['args']
    assert (
        'command' not in event_dict['args']
    )  # command should not be in serialized args

    # Common arguments in serialized form
    assert event_dict['args']['path'] == '/workspace/test.txt'
    assert event_dict['args']['impl_source'] == 'oh_aci'
    assert event_dict['args']['thought'] == 'Reading the file contents'

    # Read-specific arguments in serialized form
    assert event_dict['args']['start'] == 0
    assert event_dict['args']['end'] == -1
