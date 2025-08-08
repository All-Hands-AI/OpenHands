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

        # Instantiate all the LLM instances for routing
        llms_for_routing_config = model_routing_config.llms_for_routing
        self.llms_for_routing = {
            llm_name: LLM(config=llm_config)
            for llm_name, llm_config in llms_for_routing_config.items()
        }

        # The active LLM for the current turn
        self.active_llm = llm

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
