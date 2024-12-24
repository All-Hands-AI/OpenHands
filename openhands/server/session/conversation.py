import asyncio

from openhands.core.config import AppConfig
from openhands.events.stream import EventStream
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.server.shared import runtime_manager
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class Conversation:
    sid: str
    file_store: FileStore
    event_stream: EventStream
    runtime: Runtime | None

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: AppConfig,
    ):
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.event_stream = EventStream(sid, file_store)
        if config.security.security_analyzer:
            self.security_analyzer = options.SecurityAnalyzers.get(
                config.security.security_analyzer, SecurityAnalyzer
            )(self.event_stream)

        # Try to get existing runtime first
        self.runtime = runtime_manager.get_runtime(self.sid)

    async def connect(self):
        if self.runtime is None:
            # If no existing runtime found, create one with attach_to_existing=True
            self.runtime = await runtime_manager.create_runtime(
                event_stream=self.event_stream,
                sid=self.sid,
                attach_to_existing=True,
                headless_mode=False,
            )
        else:
            await self.runtime.connect()

    async def disconnect(self):
        if self.runtime:
            runtime_manager.destroy_runtime(self.sid)
