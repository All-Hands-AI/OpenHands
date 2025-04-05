from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.router.cost_saving.prompt import (
    CLASSIFIER_SYSTEM_MESSAGE,
    CLASSIFIER_USER_MESSAGE,
)


class CostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG = 'weak_model'

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(model_routing_config, routing_llms)

        self.classifier_llm = routing_llms[
            model_routing_config.classifier_llm_config_name
        ]
        self.weak_llm = routing_llms[self.WEAK_MODEL_CONFIG]
        self.routing_history: list[int] = []
        self.max_token_exceeded = False

    def should_route_to(self, prompt: str) -> LLM:
        if self.max_token_exceeded:
            self.routing_history.append(0)
            return self.llm

        messages = [
            {
                'role': 'system',
                'content': CLASSIFIER_SYSTEM_MESSAGE,
            },
            {
                'role': 'user',
                'content': CLASSIFIER_USER_MESSAGE.format(conversation=prompt),
            },
        ]

        try:
            response = self.classifier_llm.completion(
                messages=messages,
            )
        except Exception as e:
            print('❌ Failed to get response from classifier LLM:', e)
            self.routing_history.append(0)
            self.max_token_exceeded = True
            return self.llm

        try:
            should_route = (
                int(response['choices'][0]['message']['content'].strip()) == 1
            )
            # print('CostSavingRouter should_route:', should_route)
        except ValueError:
            print(
                '❌ Invalid response from classifier LLM, using default LLM:', response
            )
            should_route = False

        if should_route:
            self.routing_history.append(1)
            return self.weak_llm

        self.routing_history.append(0)
        return self.llm

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG not in routing_llms:
            raise ValueError(
                f'Weak LLM config {model_routing_config.reasoning_llm_config_name} not found'
            )
