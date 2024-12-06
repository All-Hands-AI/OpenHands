import asyncio
import re

from openhands.core.config import AppConfig
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.memory.condenser import MemoryCondenser
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
        asyncio.create_task(call_sync_from_async(self.runtime.close))

    def summarize_actions(self, llm: LLM) -> str:
        """Summarize the agent's actions into a short descriptive phrase.

        Args:
            llm (LLM): The language model to use for summarization.

        Returns:
            str: A short descriptive phrase summarizing the agent's actions.
        """
        events = self.event_stream.get_events()
        if not events:
            return "empty-workspace"

        # Create a prompt that asks for a short descriptive phrase
        prompt = (
            "Please summarize the following conversation into a short descriptive phrase "
            "that can be used as a filename (e.g. 'fixing-bug-in-code' or 'adding-new-feature'). "
            "The summary should be lowercase, use hyphens instead of spaces, and not include special characters.\n\n"
            "Conversation:\n"
        )
        for event in events:
            prompt += f"{event.__class__.__name__}: {str(event)}\n"

        # Use the memory condenser to get a summary
        condenser = MemoryCondenser()
        summary = condenser.condense(prompt, llm)

        # Clean up the summary to make it suitable for a filename
        summary = summary.strip().lower()
        summary = re.sub(r'[^a-z0-9-]', '-', summary)  # Replace special chars with hyphens
        summary = re.sub(r'-+', '-', summary)  # Replace multiple hyphens with single hyphen
        summary = summary.strip('-')  # Remove leading/trailing hyphens

        return summary
