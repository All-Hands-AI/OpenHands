import os
import sys
import pytest

# Ensure this repo takes precedence over any installed openhands package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from openhands.events.action import (
    Thought,
    AgentDelegateAction,
    AgentFinishAction,
    AgentRejectAction,
    ChangeAgentStateAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
    RecallAction,
    TaskTrackingAction,
)
from openhands.events.event import RecallType
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.io import json as oh_json


# ---------------------------
# event_to_dict normalization
# ---------------------------

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


# ---------------------------
# action_from_dict handling
# ---------------------------

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
        'args': {'command': 'echo 1', 'thought': {'text': 'hi', 'reasoning_content': 'rc'}},
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


def test_thought_deserialization_without_thought_but_with_top_level_rc():
    d = {
        'action': 'run',
        'args': {'command': 'echo 1', 'reasoning_content': 'only-rc'},
    }
    a = event_from_dict(d)
    assert isinstance(a.thought, Thought)
    assert a.thought.text == ''
    assert a.thought.reasoning_content == 'only-rc'


def test_thought_backwards_compat_direct_init_with_str():
    # Direct construction with a string should still work; serializer coerces to dict on wire
    a = CmdRunAction(command='echo 1', thought='plain')  # type: ignore[arg-type]
    d = event_to_dict(a)
    assert d['args']['thought'] == {'text': 'plain', 'reasoning_content': None}

    # When it comes back from wire, it becomes Thought
    a2 = event_from_dict(d)
    assert isinstance(a2.thought, Thought)
    assert a2.thought.text == 'plain'


# ---------------------------
# Round-trip across action types
# ---------------------------

@pytest.mark.parametrize(
    'action',
    [
        CmdRunAction(command='echo 1', thought=Thought(text='t', reasoning_content='r')),
        IPythonRunCellAction(code='x=1', thought=Thought(text='t', reasoning_content='r')),
        FileReadAction(path='/tmp/a', thought=Thought(text='t', reasoning_content='r')),
        FileWriteAction(path='/tmp/a', content='c', thought=Thought(text='t', reasoning_content='r')),
        FileEditAction(path='/tmp/a', command='view', thought=Thought(text='t', reasoning_content='r')),
        AgentFinishAction(final_thought='done', thought=Thought(text='t', reasoning_content='r')),
        AgentRejectAction(thought=Thought(text='t', reasoning_content='r')),
        AgentDelegateAction(agent='helper', inputs={}, thought=Thought(text='t', reasoning_content='r')),
        ChangeAgentStateAction(agent_state='running', thought=Thought(text='t', reasoning_content='r')),
        RecallAction(recall_type=RecallType.WORKSPACE_CONTEXT, thought=Thought(text='t', reasoning_content='r')),
        TaskTrackingAction(task_list=[{'id': 1, 'title': 'a'}], thought=Thought(text='t', reasoning_content='r')),
    ],
)
def test_thought_serializes_round_trip(action):
    d = event_to_dict(action)
    assert d['action'] == action.action
    assert 'args' in d
    assert isinstance(d['args'].get('thought'), dict)
    assert d['args']['thought']['text'] == 't'
    assert d['args']['thought']['reasoning_content'] == 'r'

    # json encoder should handle dicts produced by serializer
    s = oh_json.dumps(d)
    assert isinstance(s, str) and s

    # round-trip back to object
    a2 = event_from_dict(d)
    assert isinstance(a2.thought, Thought)
    assert a2.thought.text == 't'
    assert a2.thought.reasoning_content == 'r'
