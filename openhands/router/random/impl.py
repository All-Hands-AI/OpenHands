import numpy as np

from openhands.core.config.model_routing_config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.core.message import Message


class RandomRouter(BaseRouter):
    PERCENTAGE_CALLS_TO_STRONG_LLM = 0.6
    WEAK_MODEL_CONFIG = 'weak_model'

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        self.llm = llm
        self.routing_llms = routing_llms
        self.model_routing_config = model_routing_config
        np.random.seed(42)

    def should_route_to(self, messages: list[Message]) -> LLM:
        random = np.random.rand()
        if random < self.PERCENTAGE_CALLS_TO_STRONG_LLM:
            return self.llm

        return self.routing_llms[self.WEAK_MODEL_CONFIG]
