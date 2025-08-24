from datetime import datetime

from openhands.sdk.conversation import Agent, Conversation
from openhands.sdk.llm import LLM, LLMConfig
from openhands.sdk.persistence import append_event_jsonl
from openhands.sdk.types import SDKEvent


class DummyLLM(LLM):
    def __init__(self):
        pass


def test_reconstruct_messages_from_events(tmp_path, monkeypatch):
    # Prepare events with tool_call + tool_result interleaving
    conv_id = 'conv-a'
    p = tmp_path / 'sdk_events.jsonl'

    events = [
        SDKEvent(
            type='system_message',
            ts=datetime.utcnow(),
            conversation_id=conv_id,
            data={'text': 'sys'},
        ),
        SDKEvent(
            type='user_message',
            ts=datetime.utcnow(),
            conversation_id=conv_id,
            data={'text': 'u1'},
        ),
        SDKEvent(
            type='tool_call',
            ts=datetime.utcnow(),
            conversation_id=conv_id,
            data={
                'name': 'execute_bash',
                'arguments': {'command': 'echo hi'},
                'tool_call_id': 'tc1',
            },
        ),
        SDKEvent(
            type='tool_result',
            ts=datetime.utcnow(),
            conversation_id=conv_id,
            data={
                'name': 'execute_bash',
                'tool_call_id': 'tc1',
                'status': 'ok',
                'output': {'stdout': 'hi\n', 'exit_code': 0},
            },
        ),
        SDKEvent(
            type='assistant_message',
            ts=datetime.utcnow(),
            conversation_id=conv_id,
            data={'text': 'done'},
        ),
    ]
    for e in events:
        append_event_jsonl(str(p), e)

    # Build conversation and autoresume from path
    agent = Agent(llm=LLM(LLMConfig(model='dummy')), tools=[])
    conv = Conversation(agent=agent)
    conv.autoresume_from_path(str(p))

    msgs = conv.messages
    # Expect system, user, synthesized assistant with tool_calls, tool role, assistant text
    roles = [m['role'] for m in msgs]
    assert roles[0] == 'system'
    assert roles[1] == 'user'
    assert roles[2] == 'assistant' and 'tool_calls' in msgs[2]
    assert roles[3] == 'tool'
    assert roles[4] == 'assistant'
