from dataclasses import dataclass, field
from datetime import datetime, timezone

from openhands.events.event_store_abc import EventStoreABC
from openhands.storage.data_models.conversation_metadata import ConversationTrigger
from openhands.storage.data_models.conversation_status import ConversationStatus


@dataclass
class AgentLoopInfo:
    """
    Information about an agent loop - the URL on which to locate it and the event store
    """
    conversation_id: str
    url: str | None
    event_store: EventStoreABC
