import pytest

from openhands.events.action import (
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
    Thought,
)
from openhands.events.event import RecallType
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.io import json as oh_json


@pytest.mark.parametrize(
    'action',
    [
        CmdRunAction(
            command='echo 1', thought=Thought(text='t', reasoning_content='r')
        ),
        IPythonRunCellAction(
            code='x=1', thought=Thought(text='t', reasoning_content='r')
        ),
        FileReadAction(path='/tmp/a', thought=Thought(text='t', reasoning_content='r')),
        FileWriteAction(
            path='/tmp/a', content='c', thought=Thought(text='t', reasoning_content='r')
        ),
        FileEditAction(
            path='/tmp/a',
            command='view',
            thought=Thought(text='t', reasoning_content='r'),
        ),
        AgentFinishAction(
            final_thought='done', thought=Thought(text='t', reasoning_content='r')
        ),
        AgentRejectAction(thought=Thought(text='t', reasoning_content='r')),
        AgentDelegateAction(
            agent='helper', inputs={}, thought=Thought(text='t', reasoning_content='r')
        ),
        ChangeAgentStateAction(
            agent_state='running', thought=Thought(text='t', reasoning_content='r')
        ),
        RecallAction(
            recall_type=RecallType.WORKSPACE_CONTEXT,
            thought=Thought(text='t', reasoning_content='r'),
        ),
        TaskTrackingAction(
            task_list=[{'id': 1, 'title': 'a'}],
            thought=Thought(text='t', reasoning_content='r'),
        ),
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
