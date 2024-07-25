import json
import tempfile

import pytest

from opendevin.core.config import AppConfig, SandboxConfig
from opendevin.events import EventSource, EventStream
from opendevin.events.action import (
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
    NullAction,
)
from opendevin.events.observation import NullObservation
from opendevin.runtime.client.runtime import EventStreamRuntime
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
)
from opendevin.storage import get_file_store


def collect_events(stream):
    return [event for event in stream.get_events()]


def test_basic_flow():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_store = get_file_store('local', temp_dir)
        event_stream = EventStream('abc', file_store)
        event_stream.add_event(NullAction(), EventSource.AGENT)
        assert len(collect_events(event_stream)) == 1


def test_stream_storage():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_store = get_file_store('local', temp_dir)
        event_stream = EventStream('abc', file_store)
        event_stream.add_event(NullObservation(''), EventSource.AGENT)
        assert len(collect_events(event_stream)) == 1
        content = event_stream._file_store.read('sessions/abc/events/0.json')
        assert content is not None
        data = json.loads(content)
        assert 'timestamp' in data
        del data['timestamp']
        assert data == {
            'id': 0,
            'source': 'agent',
            'observation': 'null',
            'content': '',
            'extras': {},
            'message': 'No observation',
        }


def test_rehydration():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_store = get_file_store('local', temp_dir)
        event_stream = EventStream('abc', file_store)
        event_stream.add_event(NullObservation('obs1'), EventSource.AGENT)
        event_stream.add_event(NullObservation('obs2'), EventSource.AGENT)
        assert len(collect_events(event_stream)) == 2

        stream2 = EventStream('es2', file_store)
        assert len(collect_events(stream2)) == 0

        stream1rehydrated = EventStream('abc', file_store)
        events = collect_events(stream1rehydrated)
        assert len(events) == 2
        assert events[0].content == 'obs1'
        assert events[1].content == 'obs2'


@pytest.mark.asyncio
async def test_run_command():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_store = get_file_store('local', temp_dir)
        config = AppConfig(persist_sandbox=False, sandbox=SandboxConfig(box_type='ssh'))
        sid = 'test'
        cli_session = 'main' + ('_' + sid if sid else '')
        event_stream = EventStream(cli_session, file_store)
        runtime = EventStreamRuntime(config=config, event_stream=event_stream, sid=sid)
        await runtime.ainit()
        await runtime.run_action(CmdRunAction('ls -l'))


@pytest.mark.asyncio
async def test_event_stream():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_store = get_file_store('local', temp_dir)
        config = AppConfig(persist_sandbox=False, sandbox=SandboxConfig(box_type='ssh'))
        sid = 'test'
        cli_session = 'main' + ('_' + sid if sid else '')
        event_stream = EventStream(cli_session, file_store)
        runtime = EventStreamRuntime(
            config=config,
            event_stream=event_stream,
            sid=sid,
            container_image='ubuntu:22.04',
            plugins=[JupyterRequirement(), AgentSkillsRequirement()],
        )
        await runtime.ainit()

        # Test run command
        action_cmd = CmdRunAction(command='ls -l')
        await runtime.run_action(action_cmd)

        # Test run ipython
        test_code = "print('Hello, `World`!\\n')"
        action_ipython = IPythonRunCellAction(code=test_code)
        await runtime.run_action(action_ipython)

        # Test read file (file should not exist)
        action_read = FileReadAction(path='hello.sh')
        await runtime.run_action(action_read)

        # Test write file
        action_write = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
        await runtime.run_action(action_write)

        # Test read file (file should exist)
        action_read = FileReadAction(path='hello.sh')
        await runtime.run_action(action_read)

        # Test browse
        action_browse = BrowseURLAction(url='https://google.com')
        await runtime.run_action(action_browse)

        await runtime.close()
