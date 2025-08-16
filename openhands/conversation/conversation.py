import asyncio

from openhands.core.config import OpenHandsConfig
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class Conversation:
    """Transport-neutral, attachable conversation facade.

    This facade represents a single conversation identified by sid (aka
    conversation_id). It can attach to an existing runtime or create a
    lightweight runtime connection for streaming and inspection.

    It intentionally does not own the agent lifecycle; AgentSession remains the
    owner for starting/stopping the agent loop. Conversation focuses on
    attach/tail/inspect workflows and can be used by Web/CLI/Headless modes.
    """

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
        *,
        headless_mode: bool = False,
        attach_to_existing: bool = True,
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

        if runtime is not None:
            self._attach_to_existing = True
            self.runtime = runtime
        else:
            runtime_cls = get_runtime_cls(self.config.runtime)
            self.runtime = runtime_cls(
                config=config,
                event_stream=self.event_stream,
                sid=self.sid,
                attach_to_existing=attach_to_existing,
                headless_mode=headless_mode,
            )

    async def connect(self) -> None:
        if not self._attach_to_existing:
            await self.runtime.connect()

    async def disconnect(self) -> None:
        if self._attach_to_existing:
            return
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))
