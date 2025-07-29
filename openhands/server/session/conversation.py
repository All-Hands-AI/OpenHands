import asyncio

from openhands.core.config import OpenHandsConfig
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class ServerConversation:
    sid: str
    file_store: FileStore
    event_stream: EventStream
    runtime: Runtime
    user_id: str | None
    _attach_to_existing: bool = False

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: OpenHandsConfig,
        user_id: str | None,
        event_stream: EventStream | None = None,
        runtime: Runtime | None = None,
    ):
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.user_id = user_id

        if event_stream is None:
            event_stream = EventStream(sid, file_store, user_id)
        self.event_stream = event_stream

        if config.security.security_analyzer:
            self.security_analyzer = options.SecurityAnalyzers.get(
                config.security.security_analyzer, SecurityAnalyzer
            )(self.event_stream)

        if runtime:
            self._attach_to_existing = True
        else:
            runtime_cls = get_runtime_cls(self.config.runtime)
            runtime = runtime_cls(
                config=config,
                event_stream=self.event_stream,
                sid=self.sid,
                attach_to_existing=True,
                headless_mode=False,
            )
        self.runtime = runtime

    async def connect(self) -> None:
        if not self._attach_to_existing:
            await self.runtime.connect()

    async def disconnect(self) -> None:
        if self._attach_to_existing:
            return
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))
