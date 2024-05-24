from datetime import datetime

from opendevin.core.utils import json
from opendevin.events.action import MessageAction


def test_event_serialization_deserialization():
    message = MessageAction(content='This is a test.', wait_for_response=False)
    message._id = 42
    message._timestamp = datetime(2020, 1, 1, 0, 0, 0)
    serialized = json.dumps(message)
    deserialized = json.loads(serialized)
    expected = {
        'id': 42,
        'timestamp': '2020-01-01T00:00:00',
        'action': 'message',
        'message': 'This is a test.',
        'args': {
            'content': 'This is a test.',
            'wait_for_response': False,
        },
    }
    assert deserialized == expected


def test_array_serialization_deserialization():
    message = MessageAction(content='This is a test.', wait_for_response=False)
    message._id = 42
    message._timestamp = datetime(2020, 1, 1, 0, 0, 0)
    serialized = json.dumps([message])
    deserialized = json.loads(serialized)
    expected = [
        {
            'id': 42,
            'timestamp': '2020-01-01T00:00:00',
            'action': 'message',
            'message': 'This is a test.',
            'args': {
                'content': 'This is a test.',
                'wait_for_response': False,
            },
        }
    ]
    assert deserialized == expected
