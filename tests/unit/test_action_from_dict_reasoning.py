from openhands.events.action.action import Thought
from openhands.events.action.commands import CmdRunAction
from openhands.events.serialization.action import action_from_dict


def test_action_from_dict_with_thought_dict_and_rc():
    d = {
        'action': 'run',
        'args': {
            'command': 'echo 1',
            'thought': {'text': 'hi', 'reasoning_content': 'rc'},
        },
    }
    a = action_from_dict(d)
    assert isinstance(a, CmdRunAction)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == 'hi'
    assert a.thought.reasoning_content == 'rc'


def test_action_from_dict_with_thought_str_and_top_level_rc():
    d = {
        'action': 'run',
        'args': {
            'command': 'echo 1',
            'thought': 'hello',
            'reasoning_content': 'why',
        },
    }
    a = action_from_dict(d)
    assert isinstance(a, CmdRunAction)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == 'hello'
    assert a.thought.reasoning_content == 'why'


def test_action_from_dict_without_thought_but_with_top_level_rc():
    d = {
        'action': 'run',
        'args': {
            'command': 'echo 1',
            'reasoning_content': 'abc',
        },
    }
    a = action_from_dict(d)
    assert isinstance(a, CmdRunAction)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == ''
    assert a.thought.reasoning_content == 'abc'


message = "legacy"

def test_action_from_dict_with_legacy_thought_key_and_rc():
    d = {
        'action': 'run',
        'args': {
            'command': 'echo 1',
            'thought': {'thought': message},
            'reasoning_content': 'why2',
        },
    }
    a = action_from_dict(d)
    assert isinstance(a, CmdRunAction)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == message
    assert a.thought.reasoning_content == 'why2'
