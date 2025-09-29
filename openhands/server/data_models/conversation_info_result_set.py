from dataclasses import dataclass, field

from openhands.server.data_models.conversation_info import StoredConversation


@dataclass
class StoredConversationResultSet:
    results: list[StoredConversation] = field(default_factory=list)
    next_page_id: str | None = None
