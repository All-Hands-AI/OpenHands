from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.router.cost_saving.prompt import (
    CLASSIFIER_SYSTEM_MESSAGE,
    CLASSIFIER_USER_MESSAGE,
)
from transformers import AutoTokenizer
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.utils.trajectory import format_trajectory


class ThresholdBasedCostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG_NAME = 'weak_model'
    ROUTER_MODEL_CONFIG_NAME = 'classifier_model'
    TOKENIZER_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(model_routing_config, routing_llms)

        self.weak_llm = routing_llms[self.WEAK_MODEL_CONFIG_NAME]
        self.classifier_llm = routing_llms[self.ROUTER_MODEL_CONFIG_NAME]
        self.router_tokenizer = AutoTokenizer.from_pretrained(self.TOKENIZER_NAME)

        self.routing_history: list[int] = []
        self.max_token_exceeded = False

    def should_route_to(self, messages: list[Message]) -> LLM:
        # Check if `messages` exceeds context window of the weak model
        if self.weak_llm.config.max_input_tokens and self.weak_llm.get_token_count(messages) > self.weak_llm.config.max_input_tokens:
            logger.warning(
                f'Messages exceed weak model max input tokens ({self.weak_llm.config.max_input_tokens} tokens). '
                'Routing to the strong model.'
            )
            self.max_token_exceeded = True
            self.routing_history.append(0)
            return self.llm

        formatted_trajectory = format_trajectory(messages)
        if self.max_token_exceeded:
            self.routing_history.append(0)
            return self.llm

        threshold = self.score_trajectory(formatted_trajectory)
        logger.warning(f'Router probability: {threshold}')

        if threshold < self.model_routing_config.prob_threshold:
            self.routing_history.append(0)
            return self.llm

        self.routing_history.append(1)
        return self.weak_llm

    def score_trajectory(self, trajectory, **kwargs):
        """Score the trajectory using the weak model."""
        convo = self.create_conversation_prompt(trajectory)
        prompt = self.router_tokenizer.apply_chat_template([convo], tokenize=False, add_generation_prompt=True)[0]

        # Check if the prompt exceeds the context length of the router
        if len(self.router_tokenizer(prompt)['input_ids']) > self.router_tokenizer.model_max_length:
            logger.warning(
                f'Prompt exceeds model max length ({self.router_tokenizer.model_max_length} tokens). '
                'Routing to the strong model.'
            )
            self.max_token_exceeded = True
            return 0.0

        payload = {
            "input": prompt,
        }

        response = self.classifier_llm.passthrough(
            method='POST',
            endpoint='classify',
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        threshold = result['data'][0]['probs'][1] # Probability for class 1
        return threshold


    def create_conversation_prompt(self, trajectory: str) -> list:
        """Create conversation format for the tokenizer."""
        conversation = [
            {"role": "system", "content": CLASSIFIER_SYSTEM_MESSAGE},
            {"role": "user", "content": CLASSIFIER_USER_MESSAGE.format(conversation=trajectory)}
        ]
        return conversation

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG_NAME not in routing_llms:
            raise ValueError(
                f'Weak LLM config {model_routing_config.reasoning_llm_config_name} not found'
            )
        if self.ROUTER_MODEL_CONFIG_NAME not in routing_llms:
            raise ValueError(
                f'Classifier LLM config {model_routing_config.classifier_llm_config_name} not found'
            )
