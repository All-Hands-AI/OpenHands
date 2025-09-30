from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable

Json = dict[str, Any]


@dataclass
class Request:
    id: int
    method: str
    params: Any | None


@dataclass
class Response:
    id: int
    result: Any | None = None
    error: Any | None = None


@dataclass
class Notification:
    method: str
    params: Any | None


class NDJsonStdio:
    """Simple newline-delimited JSON over stdio.

    This intentionally follows the ACP typescript ndJsonStream helper for simplicity.
    """

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self._write_lock = asyncio.Lock()

    async def write(self, obj: Any) -> None:
        data = json.dumps(obj, separators=(',', ':')) + '\n'
        async with self._write_lock:
            self.writer.write(data.encode('utf-8'))
            await self.writer.drain()

    async def read(self) -> AsyncIterator[Any]:
        while not self.reader.at_eof():
            line = await self.reader.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # ignore malformed lines
                continue


class JsonRpcConnection:
    def __init__(self, stream: NDJsonStdio):
        self.stream = stream
        self._id = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._closed = asyncio.Event()
        self._tasks: set[asyncio.Task[Any]] = set()

    async def send_request(self, method: str, params: Any | None = None) -> Any:
        self._id += 1
        req_id = self._id
        fut: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        await self.stream.write(
            {'jsonrpc': '2.0', 'id': req_id, 'method': method, 'params': params}
        )
        return await fut

    async def send_notification(self, method: str, params: Any | None = None) -> None:
        await self.stream.write({'jsonrpc': '2.0', 'method': method, 'params': params})

    async def send_response(
        self, id: int, result: Any | None = None, error: Any | None = None
    ) -> None:
        if error is not None:
            await self.stream.write({'jsonrpc': '2.0', 'id': id, 'error': error})
        else:
            await self.stream.write({'jsonrpc': '2.0', 'id': id, 'result': result})

    def _create_task(self, coro: Awaitable[Any]) -> None:
        task: asyncio.Task[Any] = asyncio.create_task(coro)  # type: ignore[arg-type]
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)  # type: ignore[arg-type]

    async def serve(
        self,
        on_request: Callable[[str, Any | None], Awaitable[Any | None]],
        on_notification: Callable[[str, Any | None], Awaitable[None]] | None = None,
    ) -> None:
        async for msg in self.stream.read():
            try:
                if not isinstance(msg, dict) or msg.get('jsonrpc') != '2.0':
                    continue
                if 'method' in msg:
                    method = msg['method']
                    params = msg.get('params')
                    if 'id' in msg:
                        req_id = msg['id']

                        async def handle_req(
                            method: str = method,
                            params: Any | None = params,
                            req_id: int = req_id,
                        ) -> None:
                            try:
                                result = await on_request(method, params)
                                await self.send_response(
                                    req_id, result=result if result is not None else {}
                                )
                            except asyncio.CancelledError:
                                await self.send_response(
                                    req_id,
                                    error={'code': -32800, 'message': 'cancelled'},
                                )
                            except Exception as e:  # noqa: BLE001
                                await self.send_response(
                                    req_id, error={'code': -32603, 'message': str(e)}
                                )

                        self._create_task(handle_req())
                    else:
                        if on_notification is not None:
                            self._create_task(on_notification(method, params))
                elif 'id' in msg:
                    fut = self._pending.pop(int(msg['id']), None)
                    if fut:
                        if 'result' in msg:
                            fut.set_result(msg['result'])
                        else:
                            fut.set_exception(
                                RuntimeError(msg.get('error') or 'unknown error')
                            )
            except Exception:
                # ignore
                continue
        # Wait a brief moment for any straggling tasks
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=1.0)
        self._closed.set()

    async def wait_closed(self) -> None:
        await self._closed.wait()
