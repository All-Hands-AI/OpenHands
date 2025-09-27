"""Sandboxed conversation service for managing isolated conversation environments."""

import asyncio

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class SandboxedConversationService:
    """Service for managing sandboxed conversations with isolated runtime environments."""

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: OpenHandsConfig,
        user_id: str | None,
        event_stream: EventStream | None = None,
        runtime: Runtime | None = None,
    ):
        """Initialize a sandboxed conversation context.

        Args:
            sid: Session ID for the conversation
            file_store: File storage instance
            config: OpenHands configuration
            user_id: User ID associated with the conversation
            event_stream: Optional event stream, will be created if not provided
            runtime: Optional runtime instance, will be created if not provided
        """
        self.sid = sid
        self.config = config
        self.file_store = file_store
        self.user_id = user_id
        self._attach_to_existing = False

        if event_stream is None:
            event_stream = EventStream(sid, file_store, user_id)
        self.event_stream = event_stream

        if runtime:
            self._attach_to_existing = True
        else:
            runtime_cls = get_runtime_cls(self.config.runtime)
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
        """Connect to the sandboxed runtime environment."""
        if not self._attach_to_existing:
            logger.info(f'Connecting to sandboxed runtime for conversation {self.sid}')
            await self.runtime.connect()

    async def disconnect(self) -> None:
        """Disconnect from the sandboxed runtime environment."""
        if self._attach_to_existing:
            return

        logger.info(f'Disconnecting from sandboxed runtime for conversation {self.sid}')
        if self.event_stream:
            self.event_stream.close()
        asyncio.create_task(call_sync_from_async(self.runtime.close))

    async def execute_action(self, action):
        """Execute an action in the sandboxed environment.

        Args:
            action: The action to execute

        Returns:
            The result of the action execution
        """
        logger.debug(
            f'Executing action in sandboxed context for conversation {self.sid}'
        )
        return self.runtime.run_action(action)

    def get_working_directory(self) -> str:
        """Get the working directory of the sandboxed environment.

        Returns:
            The working directory path
        """
        return str(self.runtime.workspace_root)

    def is_connected(self) -> bool:
        """Check if the sandboxed environment is connected.

        Returns:
            True if connected, False otherwise
        """
        return (
            self.runtime.sandbox.is_connected
            if hasattr(self.runtime, 'sandbox')
            else False
        )
