from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter, ROUTER_REGISTRY
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.events.action import MessageAction


class ExtremeCostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG_NAME = 'weak_model'
    ROUTER_NAME = "extreme_cv_router"

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(model_routing_config, routing_llms)

        self.weak_llm = routing_llms[self.WEAK_MODEL_CONFIG_NAME]

        self.routing_history: list[int] = []
        self.max_token_exceeded = False

    def should_route_to(self, messages: list[Message], events: list[Event]) -> LLM:
        # Handle multimodal input
        for event in events:
            if isinstance(event, MessageAction) and event.source == 'user' and event.image_urls:
                logger.warning('Image content detected. Routing to the strong model.')
                self.routing_history.append(0)
                return self.llm

        # Check if `messages` exceeds context window of the weak model
        # FIXME: hardcode for now
        if self.weak_llm.get_token_count(messages) > 128_000:
            logger.warning(
                f'Messages exceed weak model max input tokens (128000 tokens). '
                'Routing to the strong model.'
            )
            self.max_token_exceeded = True
            self.routing_history.append(0)
            return self.llm

        if self.max_token_exceeded:
            self.routing_history.append(0)
            return self.llm

        # Use weak model otherwise
        self.routing_history.append(1)
        return self.weak_llm

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG_NAME not in routing_llms:
            raise ValueError(
                f'Weak LLM config {self.WEAK_MODEL_CONFIG_NAME} not found'
            )

# Register the router
ROUTER_REGISTRY[ExtremeCostSavingRouter.ROUTER_NAME] = ExtremeCostSavingRouter
