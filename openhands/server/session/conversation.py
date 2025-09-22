import asyncio

from openhands.core.config import OpenHandsConfig
from openhands.events.stream import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
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
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f'[TOKEN_DEBUG] ServerConversation.__init__ called: '
            f'sid={sid}, '
            f'has_runtime={runtime is not None}, '
            f'SOURCE=conversation.py (REST API)'
        )
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.user_id = user_id

        if event_stream is None:
            event_stream = EventStream(sid, file_store, user_id)
        self.event_stream = event_stream

        if runtime:
            self._attach_to_existing = True
            logger.info(
                '[TOKEN_DEBUG] ServerConversation using provided runtime, _attach_to_existing=True'
            )
        else:
            runtime_cls = get_runtime_cls(self.config.runtime)
            logger.info(
                f'[TOKEN_DEBUG] ServerConversation creating runtime: '
                f'runtime_cls={runtime_cls.__name__ if runtime_cls else None}, '
                f'attach_to_existing=True (HARDCODED in conversation.py!), '
                f'sid={self.sid}'
            )
            runtime = runtime_cls(
                llm_registry=LLMRegistry(self.config),
                config=config,
                event_stream=self.event_stream,
                sid=self.sid,
                attach_to_existing=True,
                headless_mode=False,
            )
        self.runtime = runtime

    @property
    def security_analyzer(self):
        """Access security analyzer through runtime."""
        return self.runtime.security_analyzer

    async def connect(self) -> None:
        if not self._attach_to_existing:
            await self.runtime.connect()

    async def disconnect(self) -> None:
        if self._attach_to_existing:
            return
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))
