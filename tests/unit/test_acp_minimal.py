import asyncio
import json
from typing import Any

import pytest

from openhands.acp.jsonrpc import JsonRpcConnection, NDJsonStdio
from openhands.acp.server import ACPAgentServer


class MemoryRW:
    def __init__(self):
        self.read_q: asyncio.Queue[bytes] = asyncio.Queue()
        self.write_q: asyncio.Queue[bytes] = asyncio.Queue()

    def get_streams(self):
        loop = asyncio.get_event_loop()

        async def reader_gen(reader: asyncio.StreamReader):
            while True:
                data = await self.read_q.get()
                reader.feed_data(data)
                if data == b'':
                    reader.feed_eof()
                    break

        async def make_reader():
            reader = asyncio.StreamReader()
            asyncio.create_task(reader_gen(reader))
            return reader

        class DummyProto(asyncio.Protocol):
            async def _drain_helper(self) -> None:  # satisfy StreamWriter.drain()
                return None

        async def make_writer(reader: asyncio.StreamReader):
            class DummyTransport(asyncio.Transport):
                def write(inner_self, data: bytes) -> None:
                    self.write_q.put_nowait(data)

                def is_closing(inner_self) -> bool:  # noqa: PLW3201
                    return False

            return asyncio.StreamWriter(DummyTransport(), DummyProto(), reader, loop)

        return make_reader, make_writer


async def rpc_pair():
    mem = MemoryRW()
    make_reader, make_writer = mem.get_streams()
    reader = await make_reader()
    writer = await make_writer(reader)

    stream = NDJsonStdio(reader, writer)
    rpc = JsonRpcConnection(stream)
    server = ACPAgentServer(rpc)

    async def serve():
        await rpc.serve(server.handle_request, server.handle_notification)

    task = asyncio.create_task(serve())
    return mem, task


@pytest.mark.asyncio
async def test_minimal_initialize_and_prompt():
    mem, task = await rpc_pair()

    def encode(obj: Any) -> bytes:
        return (json.dumps(obj) + '\n').encode()

    # send initialize request
    mem.read_q.put_nowait(
        encode({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}})
    )

    # read initialize response
    data = await mem.write_q.get()
    msg = json.loads(data.decode())
    assert msg['id'] == 1
    assert 'result' in msg
    assert msg['result']['protocolVersion'] == 1

    # new session
    mem.read_q.put_nowait(
        encode({'jsonrpc': '2.0', 'id': 2, 'method': 'session/new', 'params': {}})
    )
    msg = json.loads((await mem.write_q.get()).decode())
    assert msg['id'] == 2
    session_id = msg['result']['sessionId']

    # prompt
    mem.read_q.put_nowait(
        encode(
            {
                'jsonrpc': '2.0',
                'id': 3,
                'method': 'session/prompt',
                'params': {'sessionId': session_id, 'messages': []},
            }
        )
    )

    # Expect one or more session/update notifications before the result
    while True:
        msg = json.loads((await mem.write_q.get()).decode())
        if 'method' in msg:
            assert msg['method'] == 'session/update'
            assert msg['params']['sessionId'] == session_id
            continue
        # Then response to prompt
        assert msg['id'] == 3
        assert msg['result']['stopReason'] in ('end_turn', 'cancelled')
        break

    # Close
    mem.read_q.put_nowait(b'')
    await asyncio.sleep(0)  # let server finish
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
