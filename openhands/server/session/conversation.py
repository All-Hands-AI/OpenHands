import asyncio

from openhands.core.config import AppConfig
from openhands.core.schema.research import ResearchMode
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class Conversation:
    sid: str
    file_store: FileStore
    event_stream: EventStream
    runtime: Runtime | None
    user_id: str | None

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: AppConfig,
        user_id: str | None,
        research_mode: str | None = None,
    ):
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.user_id = user_id
        self.event_stream = EventStream(sid, file_store, user_id)
        if config.security.security_analyzer:
            self.security_analyzer = options.SecurityAnalyzers.get(
                config.security.security_analyzer, SecurityAnalyzer
            )(self.event_stream)

        runtime_cls = get_runtime_cls(self.config.runtime)
        if research_mode == ResearchMode.FOLLOW_UP:
            self.runtime = None
        else:
            self.runtime = runtime_cls(
                config=config,
                event_stream=self.event_stream,
                sid=self.sid,
                attach_to_existing=True,
                headless_mode=False,
            )

    async def connect(self):
        if self.runtime:
            await self.runtime.connect()

    async def disconnect(self):
        if self.event_stream:
            self.event_stream.close()
        if self.runtime:
            asyncio.create_task(call_sync_from_async(self.runtime.close))
