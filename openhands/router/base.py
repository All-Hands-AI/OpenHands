from abc import ABC, abstractmethod

from openhands.core.config import AgentConfig
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.llm.llm_registry import LLMRegistry

ROUTER_REGISTRY: dict[str, type['BaseRouter']] = {}


class BaseRouter(ABC):
    def __init__(
        self,
        agent_config: AgentConfig,
        llm_registry: LLMRegistry,
    ):
        self.llm_registry = llm_registry
        self.model_routing_config = agent_config.model_routing

        # Primary LLM for the agent
        self.llm = llm_registry.get_llm_from_agent_config('agent', agent_config)

        # Instantiate all the LLM instances for routing
        llms_for_routing_config = self.model_routing_config.llms_for_routing
        self.llms_for_routing = {
            config_name: self.llm_registry.get_llm(
                f'llm_for_routing.{config_name}', config=llm_config
            )
            for config_name, llm_config in llms_for_routing_config.items()
        }

        # The active LLM for the current turn
        self.active_llm = self.llm

    @abstractmethod
    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        """Configure the active LLM for the current turn based on the messages and events."""
        pass

    def __getattr__(self, name):
        """Delegate other attributes/methods to the active LLM."""
        return getattr(self.active_llm, name)

    @classmethod
    def from_config(
        cls, llm_registry: LLMRegistry, agent_config: AgentConfig
    ) -> 'BaseRouter':
        """Factory method to create a router instance from configuration."""
        router_cls = ROUTER_REGISTRY.get(agent_config.model_routing.router_name)
        if not router_cls:
            raise ValueError(
                f'Router {agent_config.model_routing.router_name} not found.'
            )
        return router_cls(agent_config, llm_registry)
