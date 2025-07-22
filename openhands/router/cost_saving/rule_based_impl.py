from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter, ROUTER_REGISTRY
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.events.action import MessageAction


class RuleBasedCostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG_NAME = 'weak_model'
    ROUTER_NAME = "rule_based_cv_router"

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(routing_llms)

        self.weak_llm = routing_llms[self.WEAK_MODEL_CONFIG_NAME]
        self.max_token_exceeded = False

    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        route_to_strong = False
        # Handle multimodal input
        for event in events:
            if isinstance(event, MessageAction) and event.source == 'user' and event.image_urls:
                logger.info('Image content detected. Routing to the strong model.')
                route_to_strong = True
                break

        if not route_to_strong and self.max_token_exceeded:
            route_to_strong = True

        # Check if `messages` exceeds context window of the weak model
        # Assuming the weak model has a lower context window limit compared to the strong model
        if self.weak_llm.config.max_input_tokens and self.weak_llm.get_token_count(messages) > self.weak_llm.config.max_input_tokens:
            logger.warning(
                f"Messages having {self.weak_llm.get_token_count(messages)}, exceed weak model's max input tokens ({self.weak_llm.config.max_input_tokens} tokens). "
                'Routing to the strong model.'
            )
            self.max_token_exceeded = True
            route_to_strong = True

        if route_to_strong:
            self.active_llm = self.llm
            self.routing_history.append(0)
        else:
            self.active_llm = self.weak_llm
            self.routing_history.append(1)

    def _validate_model_routing_config(
        self, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG_NAME not in routing_llms:
            raise ValueError(
                f'Weak LLM config {self.WEAK_MODEL_CONFIG_NAME} not found'
            )

# Register the router
ROUTER_REGISTRY[RuleBasedCostSavingRouter.ROUTER_NAME] = RuleBasedCostSavingRouter
