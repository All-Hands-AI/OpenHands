from dataclasses import dataclass, field

from openhands.events.event_store_abc import EventStoreABC


@dataclass
class AgentLoopInfo:
    """
    Information about an agent loop. This combines conversation metadata with
    information on whether a conversation is currently running
    """

    conversation_id: str
    agent_loop_url: str
    event_store: EventStoreABC
