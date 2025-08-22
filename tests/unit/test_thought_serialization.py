from openhands.events.action.action import Thought
from openhands.events.action.commands import CmdRunAction
from openhands.events.serialization.event import event_from_dict, event_to_dict


def test_thought_serialization_flatten_with_reasoning():
    a = CmdRunAction(command='echo 1', thought=Thought(text='t', reasoning_content='r'))
    d = event_to_dict(a)
    assert d['action'] == a.action
    assert 'args' in d
    assert isinstance(d['args']['thought'], dict)
    assert d['args']['thought']['text'] == 't'
    assert d['args']['thought']['reasoning_content'] == 'r'

    # Round-trip back
    a2 = event_from_dict(d)
    assert isinstance(a2.thought, Thought)
    assert a2.thought.text == 't'
    assert a2.thought.reasoning_content == 'r'


def test_thought_deserialization_from_string_plus_rc():
    d = {
        'action': 'run',
        'args': {'command': 'echo 1', 'thought': 'hello', 'reasoning_content': 'why'},
    }
    a = event_from_dict(d)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == 'hello'
    assert a.thought.reasoning_content == 'why'


def test_thought_deserialization_from_dict_text_key():
    d = {
        'action': 'run',
        'args': {
            'command': 'echo 1',
            'thought': {'text': 'hi', 'reasoning_content': 'rc'},
        },
    }
    a = event_from_dict(d)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == 'hi'
    assert a.thought.reasoning_content == 'rc'


def test_thought_deserialization_from_dict_legacy_thought_key():
    d = {
        'action': 'run',
        'args': {'command': 'echo 1', 'thought': {'thought': 'legacy'}},
    }
    a = event_from_dict(d)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == 'legacy'
    assert a.thought.reasoning_content is None


def test_thought_backwards_compat_direct_init_with_str():
    # Direct construction with a string should still work via __str__ accessors elsewhere
    a = CmdRunAction(command='echo 1', thought='plain')  # type: ignore[arg-type]
    d = event_to_dict(a)  # serializer should keep thought as string on wire
    assert d['args']['thought'] == 'plain'

    # When it comes back from wire, it becomes Thought
    a2 = event_from_dict(d)
    assert isinstance(a2.thought, Thought)
    assert a2.thought.text == 'plain'
