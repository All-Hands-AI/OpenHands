from dataclasses import dataclass

from openhands.events.event_store_abc import EventStoreABC


@dataclass
class AgentLoopInfo:
    """
    Information about an agent loop - the URL on which to locate it and the event store
    """
    conversation_id: str
    url: str | None
    session_api_key: str | None
    event_store: EventStoreABC
