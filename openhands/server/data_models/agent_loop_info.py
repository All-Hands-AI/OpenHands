from dataclasses import dataclass, field

from openhands.events.event_store_abc import EventStoreABC
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.storage.data_models.conversation_status import ConversationStatus


@dataclass
class AgentLoopInfo:
    """
    Information about an agent loop - the URL on which to locate it and the event store
    """

    conversation_id: str
    url: str | None
    session_api_key: str | None
    event_store: EventStoreABC | None
    status: ConversationStatus = field(default=ConversationStatus.RUNNING)
    runtime_status: RuntimeStatus | None = None
