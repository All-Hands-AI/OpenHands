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
        model_routing_config: ModelRoutingConfig,
    ):
        self.llm = llm
        self.model_routing_config = model_routing_config

        # Instantiate all the routing LLM instances
        routing_llms_config = model_routing_config.routing_llms
        self.routing_llms = {
            llm_name: LLM(config=llm_config)
            for llm_name, llm_config in routing_llms_config.items()
        }

        # The active LLM for the current turn
        self.active_llm = llm

        # Tracking data
        self.routing_history: list[int] = []

    @abstractmethod
    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        """Configure the active LLM for the current turn based on the messages and events."""
        pass
