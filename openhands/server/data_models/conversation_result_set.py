from dataclasses import dataclass, field

from openhands.server.data_models.conversation_info import ConversationInfo


@dataclass
class ConversationResultSet:
    results: list[ConversationInfo] = field(default_factory=list)
    next_page_id: str | None = None
