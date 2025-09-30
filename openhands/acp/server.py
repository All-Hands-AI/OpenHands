from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from openhands.acp.jsonrpc import JsonRpcConnection, NDJsonStdio
from openhands.core.logger import openhands_logger as logger

PROTOCOL_VERSION = 1


@dataclass
class SessionState:
    pending_task: asyncio.Task | None = None


class ACPAgentServer:
    """Minimal ACP adapter to expose OpenHands as an ACP Agent over stdio NDJSON.

    Implements initialize, session/new, session/prompt and session/cancel,
    and provides client-facing notifications session/update and requests
    like session/request_permission in the future. This is a minimal MVP to
    integrate with Zed ACP client.
    """

    def __init__(self, rpc: JsonRpcConnection):
        self.rpc = rpc
        self.sessions: dict[str, SessionState] = {}

    async def handle_request(self, method: str, params: Any | None) -> Any | None:
        if method == 'initialize':
            return await self._initialize(params)
        if method == 'session/new':
            return await self._session_new(params)
        if method == 'session/prompt':
            return await self._session_prompt(params)
        if method == 'session/cancel':
            # Spec: cancel is a notification, but handle gracefully if sent as request
            await self._session_cancel(params)
            return {}
        if method == 'authenticate':
            # No-op for now
            return {}
        if method == 'session/set_mode':
            return {}
        raise RuntimeError(f'Method not implemented: {method}')

    async def handle_notification(self, method: str, params: Any | None) -> None:
        if method == 'session/cancel':
            await self._session_cancel(params)

    async def _initialize(self, params: dict[str, Any] | None) -> dict[str, Any]:
        return {
            'protocolVersion': PROTOCOL_VERSION,
            'agentCapabilities': {
                'loadSession': False,
            },
            'promptCapabilities': {
                'supportsImage': True,
                'supportsAudio': False,
                'supportsResources': True,
            },
        }

    async def _session_new(self, params: dict[str, Any] | None) -> dict[str, Any]:
        # Client may provide preferred model or workspace details; ignore for MVP
        session_id = await self._generate_session_id()
        self.sessions[session_id] = SessionState()
        return {'sessionId': session_id}

    async def _session_prompt(self, params: dict[str, Any] | None) -> dict[str, Any]:
        assert params is not None
        session_id = params.get('sessionId', '')
        # Accept either 'messages' (python test harness) or 'prompt' (ACP TS client)
        _messages = (
            params.get('messages') if 'messages' in params else params.get('prompt', [])
        )
        # For MVP we just echo a text agent message chunk and end_turn
        state = self.sessions.get(session_id)
        if state is None:
            raise RuntimeError(f'Unknown session {session_id}')

        # cancel any pending prompt
        if state.pending_task and not state.pending_task.done():
            state.pending_task.cancel()
            try:
                await state.pending_task
            except Exception:  # noqa: BLE001
                pass

        async def run_turn() -> None:
            try:
                await self.rpc.send_notification(
                    'session/update',
                    {
                        'sessionId': session_id,
                        'update': {
                            'sessionUpdate': 'agent_message_chunk',
                            'content': {
                                'type': 'text',
                                'text': 'OpenHands is thinking...',
                            },
                        },
                    },
                )
                await asyncio.sleep(0.2)
                await self.rpc.send_notification(
                    'session/update',
                    {
                        'sessionId': session_id,
                        'update': {
                            'sessionUpdate': 'agent_message_chunk',
                            'content': {
                                'type': 'text',
                                'text': 'This is a minimal ACP adapter.',
                            },
                        },
                    },
                )
            except asyncio.CancelledError:
                # Send nothing more
                raise
            except Exception as e:  # noqa: BLE001
                logger.exception('Error in prompt run: %s', e)

        task = asyncio.create_task(run_turn())
        state.pending_task = task
        try:
            await task
            stop_reason = 'end_turn'
        except asyncio.CancelledError:
            stop_reason = 'cancelled'
        return {'stopReason': stop_reason}

    async def _session_cancel(self, params: dict[str, Any] | None) -> None:
        if not params:
            return
        session_id = params.get('sessionId')
        if not session_id:
            return
        state = self.sessions.get(session_id)
        if state and state.pending_task and not state.pending_task.done():
            state.pending_task.cancel()

    async def _generate_session_id(self) -> str:
        # Simple increasing counter based id
        return f'sess-{len(self.sessions) + 1:04d}'


async def run_stdio_server() -> None:
    import sys

    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
    write_transport, write_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(write_transport, write_protocol, reader, loop)

    stream = NDJsonStdio(reader, writer)
    rpc = JsonRpcConnection(stream)
    server = ACPAgentServer(rpc)
    await rpc.serve(server.handle_request, server.handle_notification)
