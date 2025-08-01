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

    def __getattr__(self, name):
        """Delegate other attributes/methods to the active LLM."""
        return getattr(self.active_llm, name)

    @classmethod
    def from_config(
        cls, llm: LLM, model_routing_config: ModelRoutingConfig
    ) -> 'BaseRouter':
        """Factory method to create a router instance from configuration."""
        router_cls = ROUTER_REGISTRY.get(model_routing_config.router_name)
        if not router_cls:
            raise ValueError(f'Router {model_routing_config.router_name} not found.')
        return router_cls(llm, model_routing_config)
