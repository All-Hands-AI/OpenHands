from abc import ABC, abstractmethod

from openhands.core.config.model_routing_config import ModelRoutingConfig
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.llm.llm import LLM

ROUTER_REGISTRY: dict[str, type['BaseRouter']] = {}


class BaseRouter(ABC):
    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        self.llm = llm
        self.routing_llms = routing_llms
        self.model_routing_config = model_routing_config

        # The active LLM for the current turn
        self.active_llm = llm

        # Tracking data
        self.routing_history: list[int] = []

    @abstractmethod
    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        """Configure the active LLM for the current turn based on the messages and events."""
        pass
