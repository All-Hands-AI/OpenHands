from __future__ import annotations

from dataclasses import dataclass

from openhands.storage.locations import (
    get_conversation_agent_state_filename,
    get_conversation_dir,
    get_conversation_event_filename,
    get_conversation_events_dir,
    get_conversation_init_data_filename,
    get_conversation_llm_registry_filename,
    get_conversation_metadata_filename,
    get_conversation_stats_filename,
)


@dataclass(frozen=True)
class ConversationPaths:
    sid: str
    user_id: str | None = None

    def conversation_dir(self) -> str:
        return get_conversation_dir(self.sid, self.user_id)

    def events_dir(self) -> str:
        return get_conversation_events_dir(self.sid, self.user_id)

    def event_filename(self, id: int) -> str:
        return get_conversation_event_filename(self.sid, id, self.user_id)

    def metadata_filename(self) -> str:
        return get_conversation_metadata_filename(self.sid, self.user_id)

    def init_data_filename(self) -> str:
        return get_conversation_init_data_filename(self.sid, self.user_id)

    def agent_state_filename(self) -> str:
        return get_conversation_agent_state_filename(self.sid, self.user_id)

    def llm_registry_filename(self) -> str:
        return get_conversation_llm_registry_filename(self.sid, self.user_id)

    def stats_filename(self) -> str:
        return get_conversation_stats_filename(self.sid, self.user_id)

    def event_cache_filename(self, start: int, end: int) -> str:
        return f'{self.conversation_dir()}event_cache/{start}-{end}.json'
