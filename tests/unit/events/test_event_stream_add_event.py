import json

from openhands.events import EventSource
from openhands.events.event import RecallType
from openhands.events.observation.agent import MicroagentKnowledge, RecallObservation
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.events.stream import EventStream
from openhands.storage import get_file_store
from openhands.storage.locations import get_conversation_event_filename


def _read_persisted(stream: EventStream, event_id: int) -> dict:
    content = stream.file_store.read(
        get_conversation_event_filename(stream.sid, event_id, stream.user_id)
    )
    assert content is not None
    return json.loads(content)


def test_redacts_secrets_in_lists(tmp_path):
    fs = get_file_store('local', str(tmp_path))
    stream = EventStream('s', fs)
    stream.set_secrets({'OPENAI_API_KEY': 'sk-abc'})

    # Put secret inside a list of nested dataclasses (microagent_knowledge)
    obs = RecallObservation(
        content='c',
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(name='agent1', trigger='t', content='keep sk-abc')
        ],
    )

    stream.add_event(obs, EventSource.AGENT)
    data = _read_persisted(stream, 0)

    # Verify secret inside list was redacted
    assert (
        data['extras']['microagent_knowledge'][0]['content'] == 'keep <secret_hidden>'
    )


def test_canonicalization_round_trip(tmp_path):
    fs = get_file_store('local', str(tmp_path))
    stream = EventStream('s', fs)

    # Include nested dataclass list to exercise canonicalization
    obs = RecallObservation(
        content='c',
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[MicroagentKnowledge(name='k', trigger='t', content='v')],
    )

    stream.add_event(obs, EventSource.AGENT)

    persisted = _read_persisted(stream, 0)

    # Remove timestamp for comparison
    ts = persisted.pop('timestamp', None)
    assert ts is not None

    # Canonicalization invariant: event_to_dict(event_from_dict(persisted)) == persisted
    canon = event_to_dict(event_from_dict(persisted))
    # event_to_dict adds timestamp back if present on object; our persisted lacks it now
    canon.pop('timestamp', None)
    assert canon == persisted
