from datetime import datetime

from openhands.sdk.persistence import append_event_jsonl, read_events_jsonl
from openhands.sdk.types import SDKEvent


def test_jsonl_roundtrip(tmp_path):
    p = tmp_path / 'sdk_events.jsonl'
    conv_id = 'conv-1'
    ev1 = SDKEvent(
        type='system_message',
        ts=datetime.utcnow(),
        conversation_id=conv_id,
        data={'text': 'sys'},
    )
    ev2 = SDKEvent(
        type='user_message',
        ts=datetime.utcnow(),
        conversation_id=conv_id,
        data={'text': 'hello'},
    )
    append_event_jsonl(str(p), ev1)
    append_event_jsonl(str(p), ev2)

    events = read_events_jsonl(str(p))
    assert len(events) == 2
    assert events[0].type == 'system_message'
    assert events[1].data['text'] == 'hello'
