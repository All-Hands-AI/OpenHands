from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openhands.controller.agent_controller import AgentController
    from openhands.events.stream import EventStream
    from openhands.llm.llm import LLM
    from openhands.runtime.base import Runtime


@dataclass
class Conversation:
    """Main interface for conversations in OpenHands.

    This class serves as a container for all the components needed for a conversation
    between a user and an OpenHands agent.

    Attributes:
        conversation_id: Unique identifier for the conversation
        runtime: Runtime environment where the agent operates
        llm: Language model used by the agent
        event_stream: Stream of events (actions and observations) in the conversation
        agent_controller: Controller that manages the agent's behavior and state
    """

    conversation_id: str
    runtime: 'Runtime'
    llm: 'LLM'
    event_stream: 'EventStream'
    agent_controller: 'AgentController'
