import asyncio

from openhands.core.config import AppConfig
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
    runtime: Runtime

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

        runtime_cls = get_runtime_cls(self.config.runtime)
        self.runtime = runtime_cls(
            config=config,
            event_stream=self.event_stream,
            sid=self.sid,
            attach_to_existing=True,
            headless_mode=False,
        )

    async def connect(self):
        await self.runtime.connect()

    async def disconnect(self):
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))

    def get_metrics(self):
        """Get metrics directly from the runtime's state.

        This method retrieves metrics from the runtime's state object rather than
        reconstructing them from events, providing a more accurate representation
        of costs and token usage, including those not associated with events.

        Returns:
            Metrics: The metrics object containing accumulated cost and token usage data.
            Returns None if no metrics are available or if the runtime has no state.
        """
        try:
            if hasattr(self.runtime, 'state') and self.runtime.state:
                return self.runtime.state.metrics
            return None
        except Exception as e:
            from openhands.core.logger import openhands_logger as logger

            logger.error(f'Error retrieving metrics from runtime state: {e}')
            return None
