from openhands.core.config import ModelRoutingConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.events.action import MessageAction
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.router.base import ROUTER_REGISTRY, BaseRouter


class MultimodalRouter(BaseRouter):
    SECONDARY_MODEL_CONFIG_NAME = 'secondary_model'
    ROUTER_NAME = 'multimodal_router'

    def __init__(
        self,
        llm: LLM,
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, model_routing_config)

        self._validate_model_routing_config(self.routing_llms)

        self.secondary_llm = self.routing_llms[self.SECONDARY_MODEL_CONFIG_NAME]
        self.max_token_exceeded = False

    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        route_to_primary = False
        # Handle multimodal input
        for event in events:
            if (
                isinstance(event, MessageAction)
                and event.source == 'user'
                and event.image_urls
            ):
                logger.info('Image content detected. Routing to the primary model.')
                route_to_primary = True
                break

        if not route_to_primary and self.max_token_exceeded:
            route_to_primary = True

        # Check if `messages` exceeds context window of the secondary model
        # Assuming the secondary model has a lower context window limit compared to the primary model
        if (
            self.secondary_llm.config.max_input_tokens
            and self.secondary_llm.get_token_count(messages)
            > self.secondary_llm.config.max_input_tokens
        ):
            logger.warning(
                f"Messages having {self.secondary_llm.get_token_count(messages)}, exceed secondary model's max input tokens ({self.secondary_llm.config.max_input_tokens} tokens). "
                'Routing to the primary model.'
            )
            self.max_token_exceeded = True
            route_to_primary = True

        if route_to_primary:
            logger.warning('Routing to the primary model...')
            self.active_llm = self.llm
        else:
            self.active_llm = self.secondary_llm

    def _validate_model_routing_config(self, routing_llms: dict[str, LLM]):
        if self.SECONDARY_MODEL_CONFIG_NAME not in routing_llms:
            raise ValueError(
                f'Secondary LLM config {self.SECONDARY_MODEL_CONFIG_NAME} not found'
            )


# Register the router
ROUTER_REGISTRY[MultimodalRouter.ROUTER_NAME] = MultimodalRouter
