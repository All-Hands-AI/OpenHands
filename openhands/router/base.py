from abc import ABC, abstractmethod

from openhands.core.config.model_routing_config import ModelRoutingConfig
from openhands.core.message import Message
from openhands.llm.llm import LLM


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

    @abstractmethod
    def should_route_to(self, messages: list[Message]) -> LLM:
        pass
